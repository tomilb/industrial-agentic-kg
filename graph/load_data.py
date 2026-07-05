"""Aplica graph/schema.cypher y carga los CSVs de data-gen/output/ a Neo4j.

Idempotente: toda escritura usa MERGE anclado en el id de negocio de cada
nodo (o en el patrón Maquina-fecha para RegistroProduccion), así que
ejecutar este script varias veces no duplica nodos ni relaciones.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

SCHEMA_PATH = Path(__file__).parent / "schema.cypher"
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data-gen" / "output"


def get_driver() -> Driver:
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def dividir_sentencias(texto: str) -> list[str]:
    """Trocea schema.cypher en sentencias individuales, descartando
    comentarios de línea (//) y fragmentos vacíos."""
    sin_comentarios = "\n".join(
        linea for linea in texto.splitlines() if not linea.strip().startswith("//")
    )
    return [s.strip() for s in sin_comentarios.split(";") if s.strip()]


def aplicar_schema(driver: Driver, schema_path: Path = SCHEMA_PATH) -> None:
    sentencias = dividir_sentencias(schema_path.read_text(encoding="utf-8"))
    with driver.session() as session:
        for sentencia in sentencias:
            session.run(sentencia)


def leer_csv(data_dir: Path, nombre: str) -> list[dict]:
    """Lee un CSV a lista de dicts con tipos nativos de Python.

    pandas.read_csv().to_dict() deja escalares numpy (int64/float64) que
    el driver de Neo4j no serializa correctamente como parámetros de
    query; el roundtrip por JSON los normaliza a int/float/str nativos.
    """
    df = pd.read_csv(data_dir / f"{nombre}.csv")
    return json.loads(df.to_json(orient="records"))


def derivar_pares_precede_a(estaciones_rows: list[dict]) -> list[dict]:
    """A partir de la columna 'orden', arma los pares consecutivos
    (E1->E2->E3->...) que se cargan como relaciones PRECEDE_A."""
    ordenadas = sorted(estaciones_rows, key=lambda r: r["orden"])
    return [
        {"actual": actual["id"], "siguiente": siguiente["id"]}
        # strict=False a propósito: ordenadas y ordenadas[1:] difieren en
        # longitud por diseño (pares consecutivos), no es un bug.
        for actual, siguiente in zip(ordenadas, ordenadas[1:], strict=False)
    ]


def cargar_lineas(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MERGE (l:Linea {id: row.id})
            SET l.nombre = row.nombre
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def cargar_estaciones(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (l:Linea {id: row.linea_id})
            MERGE (e:Estacion {id: row.id})
            SET e.nombre = row.nombre
            MERGE (l)-[:TIENE_ESTACION]->(e)
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def cargar_precede_a(driver: Driver, estaciones_rows: list[dict]) -> None:
    pares = derivar_pares_precede_a(estaciones_rows)

    def _tx(tx, pares):
        tx.run(
            """
            UNWIND $pares AS par
            MATCH (a:Estacion {id: par.actual}), (b:Estacion {id: par.siguiente})
            MERGE (a)-[:PRECEDE_A]->(b)
            """,
            pares=pares,
        )

    with driver.session() as session:
        session.execute_write(_tx, pares)


def cargar_maquinas(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (e:Estacion {id: row.estacion_id})
            MERGE (m:Maquina {id: row.id})
            SET m.nombre = row.nombre,
                m.coste_adquisicion = row.coste_adquisicion,
                m.capacidad_ud_h = row.capacidad_ud_h,
                m.oee_actual = row.oee_actual,
                m.coste_mantenimiento_anual = row.coste_mantenimiento_anual,
                m.consumo_kwh = row.consumo_kwh,
                m.vida_util_anos = row.vida_util_anos,
                m.anos_en_servicio = row.anos_en_servicio
            MERGE (e)-[:OPERA]->(m)
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def cargar_candidatas(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (m:Maquina {id: row.maquina_id})
            MERGE (c:MaquinaCandidata {id: row.id})
            SET c.nombre = row.nombre,
                c.coste_adquisicion = row.coste_adquisicion,
                c.capacidad_ud_h = row.capacidad_ud_h,
                c.coste_mantenimiento_anual = row.coste_mantenimiento_anual,
                c.consumo_kwh = row.consumo_kwh,
                c.vida_util_anos = row.vida_util_anos,
                c.mejora_capacidad_pct = row.mejora_capacidad_pct
            MERGE (m)-[:PUEDE_SUSTITUIRSE_POR]->(c)
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def cargar_registros(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (m:Maquina {id: row.maquina_id})
            MERGE (m)-[:REGISTRA]->(r:RegistroProduccion {fecha: date(row.fecha)})
            SET r.unidades = row.unidades,
                r.tiempo_ciclo_s = row.tiempo_ciclo_s,
                r.paradas_min = row.paradas_min,
                r.defectos = row.defectos
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def cargar_todo(driver: Driver, data_dir: Path = DEFAULT_DATA_DIR) -> None:
    lineas = leer_csv(data_dir, "lineas")
    estaciones = leer_csv(data_dir, "estaciones")
    maquinas = leer_csv(data_dir, "maquinas")
    candidatas = leer_csv(data_dir, "maquinas_candidatas")
    registros = leer_csv(data_dir, "registros_produccion")

    cargar_lineas(driver, lineas)
    cargar_estaciones(driver, estaciones)
    cargar_precede_a(driver, estaciones)
    cargar_maquinas(driver, maquinas)
    cargar_candidatas(driver, candidatas)
    cargar_registros(driver, registros)


def main() -> None:
    driver = get_driver()
    try:
        aplicar_schema(driver)
        cargar_todo(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
