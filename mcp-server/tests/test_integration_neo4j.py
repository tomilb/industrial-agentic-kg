"""Tests de integración contra un Neo4j real (efímero, vía testcontainers).

Necesitan Docker. Se marcan @pytest.mark.integration para poder correrlos
por separado de los tests rápidos con driver falso:
    pytest mcp-server/tests/test_integration_neo4j.py -m integration

El contenedor es completamente aparte del Neo4j de desarrollo
(docker-compose.yml / industrial-kg-neo4j): testcontainers expone el
puerto a uno aleatorio del host, no al 7687 fijo, y lo destruye al
terminar. Si Docker no está disponible, el fixture hace pytest.skip en
vez de fallar con un error.
"""

from __future__ import annotations

from typing import Any

import pytest
import server
from load_data import (
    aplicar_schema,
    cargar_candidatas,
    cargar_estaciones,
    cargar_lineas,
    cargar_maquinas,
    cargar_precede_a,
    cargar_registros,
)
from testcontainers.neo4j import Neo4jContainer


@pytest.fixture(scope="module")
def neo4j_driver():
    try:
        container = Neo4jContainer("neo4j:5.24-community", password="test-password")
        container.start()
    except Exception as e:
        pytest.skip(f"Docker no disponible para tests de integración: {e}")

    driver = container.get_driver()
    try:
        yield driver
    finally:
        driver.close()
        container.stop()


def _cargar_fixture_minima(driver) -> None:
    """2 estaciones (no 5), 1 candidata, 2 días de registros por máquina —
    suficiente para ejercitar los 5 tipos de relación del esquema y probar
    detectar_cuello_botella contra Cypher/driver reales, sin duplicar el
    dataset completo de data-gen. Números redondos: el oee empírico
    resultante coincide exactamente con oee_actual (verificable a mano)."""
    aplicar_schema(driver)

    lineas = [{"id": "L1", "nombre": "Línea de prueba"}]
    estaciones = [
        {"id": "E1", "linea_id": "L1", "nombre": "Estación A", "orden": 1},
        {"id": "E2", "linea_id": "L1", "nombre": "Estación B", "orden": 2},
    ]
    maquinas = [
        {
            "id": "M1",
            "estacion_id": "E1",
            "nombre": "Máquina A",
            "capacidad_ud_h": 600.0,
            "oee_actual": 0.85,
            "coste_adquisicion": 100_000.0,
            "coste_mantenimiento_anual": 5_000.0,
            "consumo_kwh": 5.0,
            "vida_util_anos": 10,
        },
        {
            "id": "M2",
            "estacion_id": "E2",
            "nombre": "Máquina B",
            "capacidad_ud_h": 400.0,
            "oee_actual": 0.75,
            "coste_adquisicion": 70_000.0,
            "coste_mantenimiento_anual": 5_000.0,
            "consumo_kwh": 3.0,
            "vida_util_anos": 8,
        },
    ]
    candidatas = [
        {
            "id": "C2",
            "maquina_id": "M2",
            "nombre": "Máquina B mejorada",
            "capacidad_ud_h": 650.0,
            "coste_adquisicion": 150_000.0,
            "coste_mantenimiento_anual": 5_000.0,
            "consumo_kwh": 3.0,
            "vida_util_anos": 8,
            "mejora_capacidad_pct": 62.0,
        },
    ]
    registros = [
        {
            "maquina_id": "M1",
            "fecha": "2026-06-01",
            "unidades": 8160,  # 8160/(600*16) = 0.85 = oee_actual
            "tiempo_ciclo_s": 7.06,
            "paradas_min": 0.0,
            "defectos": 0,
        },
        {
            "maquina_id": "M1",
            "fecha": "2026-06-02",
            "unidades": 8160,
            "tiempo_ciclo_s": 7.06,
            "paradas_min": 0.0,
            "defectos": 0,
        },
        {
            "maquina_id": "M2",
            "fecha": "2026-06-01",
            "unidades": 4800,  # 4800/(400*16) = 0.75 = oee_actual
            "tiempo_ciclo_s": 12.0,
            "paradas_min": 0.0,
            "defectos": 0,
        },
        {
            "maquina_id": "M2",
            "fecha": "2026-06-02",
            "unidades": 4800,
            "tiempo_ciclo_s": 12.0,
            "paradas_min": 0.0,
            "defectos": 0,
        },
    ]

    cargar_lineas(driver, lineas)
    cargar_estaciones(driver, estaciones)
    cargar_precede_a(driver, estaciones)
    cargar_maquinas(driver, maquinas)
    cargar_candidatas(driver, candidatas)
    cargar_registros(driver, registros)


def _contar_nodos_y_relaciones(driver) -> dict[str, Any]:
    with driver.session() as session:
        nodos = {
            r["tipo"]: r["n"]
            for r in session.run("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS n")
        }
        relaciones = {
            r["tipo"]: r["n"]
            for r in session.run("MATCH ()-[rel]->() RETURN type(rel) AS tipo, count(*) AS n")
        }
    return {**nodos, **relaciones}


@pytest.mark.integration
def test_carga_doble_no_duplica_nodos_ni_relaciones(neo4j_driver):
    _cargar_fixture_minima(neo4j_driver)
    conteo_1 = _contar_nodos_y_relaciones(neo4j_driver)

    _cargar_fixture_minima(neo4j_driver)  # segunda carga, sin borrar nada entre medias
    conteo_2 = _contar_nodos_y_relaciones(neo4j_driver)

    assert conteo_1 == conteo_2
    assert conteo_1["Estacion"] == 2
    assert conteo_1["Maquina"] == 2
    assert conteo_1["MaquinaCandidata"] == 1
    assert conteo_1["TIENE_ESTACION"] == 2
    assert conteo_1["OPERA"] == 2
    assert conteo_1["PRECEDE_A"] == 1
    assert conteo_1["PUEDE_SUSTITUIRSE_POR"] == 1
    assert conteo_1["REGISTRA"] == 4


@pytest.mark.integration
def test_detectar_cuello_botella_contra_neo4j_real(neo4j_driver):
    _cargar_fixture_minima(neo4j_driver)  # idempotente, no pasa nada si ya estaba cargado

    resultado = server._detectar_cuello_botella(neo4j_driver, "L1", "2026-06-01", "2026-06-02")

    restriccion = next(e for e in resultado.estaciones if e.es_restriccion)
    assert restriccion.estacion_id == "E2"
    assert restriccion.capacidad_efectiva == pytest.approx(300.0)
    assert restriccion.fuente_oee == "empirico"

    no_restriccion = next(e for e in resultado.estaciones if not e.es_restriccion)
    assert no_restriccion.estacion_id == "E1"
    assert no_restriccion.capacidad_efectiva == pytest.approx(510.0)
