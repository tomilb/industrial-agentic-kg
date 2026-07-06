"""Tests de integración de consultar_manual_tecnico contra un Neo4j real
(efímero, vía testcontainers) — usan contenido REAL de manuales/M3.md y
manuales/M4.md (no un fixture sintético), porque aquí lo que interesa
verificar es relevancia semántica real y que el filtro por maquina_id no
mezcla contenido de otra máquina, algo que un fixture inventado no
probaría de forma convincente.

Necesitan Docker (neo4j_driver, en conftest.py) y descargan/cargan el
modelo real de embeddings (no hay fake aquí a propósito).
"""

from __future__ import annotations

import pytest
import server
from load_data import aplicar_schema, cargar_estaciones, cargar_lineas, cargar_maquinas
from load_manuals import (
    MODELO_EMBEDDINGS,
    calcular_embeddings,
    cargar_manual_chunks,
    construir_chunks,
)
from sentence_transformers import SentenceTransformer


@pytest.fixture(scope="module")
def modelo_embeddings():
    return SentenceTransformer(MODELO_EMBEDDINGS)


@pytest.fixture(scope="module")
def manuales_cargados(neo4j_driver, modelo_embeddings):
    aplicar_schema(neo4j_driver)

    # cargar_manual_chunks hace MATCH sobre maquina_id: los nodos Maquina
    # M3/M4 tienen que existir ya (con su Estacion/Linea) antes de cargar
    # los chunks, si no el MATCH falla en silencio y no se crea nada.
    cargar_lineas(neo4j_driver, [{"id": "L1", "nombre": "Línea de prueba"}])
    cargar_estaciones(
        neo4j_driver,
        [
            {"id": "E3", "linea_id": "L1", "nombre": "Inspección óptica (AOI)", "orden": 1},
            {"id": "E4", "linea_id": "L1", "nombre": "Ensamblaje de carcasa", "orden": 2},
        ],
    )
    cargar_maquinas(
        neo4j_driver,
        [
            {
                "id": "M3",
                "estacion_id": "E3",
                "nombre": "AOI de gama básica",
                "capacidad_ud_h": 400.0,
                "oee_actual": 0.75,
                "coste_adquisicion": 70_000.0,
                "coste_mantenimiento_anual": 5_000.0,
                "consumo_kwh": 3.0,
                "vida_util_anos": 8,
            },
            {
                "id": "M4",
                "estacion_id": "E4",
                "nombre": "Cobot de ensamblaje",
                "capacidad_ud_h": 500.0,
                "oee_actual": 0.88,
                "coste_adquisicion": 45_000.0,
                "coste_mantenimiento_anual": 4_000.0,
                "consumo_kwh": 2.0,
                "vida_util_anos": 10,
            },
        ],
    )

    chunks = [c for c in construir_chunks() if c["maquina_id"] in ("M3", "M4")]
    cargar_manual_chunks(neo4j_driver, calcular_embeddings(chunks, modelo_embeddings))
    return neo4j_driver


@pytest.mark.integration
def test_consultar_manual_tecnico_devuelve_contenido_real_de_m3(
    manuales_cargados, modelo_embeddings
):
    resultado = server._consultar_manual_tecnico(
        manuales_cargados,
        modelo_embeddings,
        "M3",
        "¿Qué mantenimiento necesita la estación de inspección óptica?",
    )

    assert resultado.maquina_id == "M3"
    assert len(resultado.chunks) > 0
    texto = " ".join(c.texto for c in resultado.chunks).lower()
    # vocabulario real de manuales/M3.md (sección Mantenimiento preventivo)
    assert "lente" in texto or "iluminación" in texto


@pytest.mark.integration
def test_consultar_manual_tecnico_no_mezcla_contenido_de_otra_maquina(
    manuales_cargados, modelo_embeddings
):
    resultado = server._consultar_manual_tecnico(
        manuales_cargados,
        modelo_embeddings,
        "M3",
        "¿Qué mantenimiento necesita la estación de inspección óptica?",
    )

    texto = " ".join(c.texto for c in resultado.chunks).lower()
    # vocabulario real de manuales/M4.md — no debe colarse al filtrar por M3
    assert "pinza" not in texto
    assert "cobot" not in texto
