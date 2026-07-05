import load_data
import pandas as pd


def test_precede_a_deriva_pares_consecutivos_por_orden():
    estaciones = [
        {"id": "E3", "orden": 3},
        {"id": "E1", "orden": 1},
        {"id": "E4", "orden": 4},
        {"id": "E2", "orden": 2},
    ]

    pares = load_data.derivar_pares_precede_a(estaciones)

    assert pares == [
        {"actual": "E1", "siguiente": "E2"},
        {"actual": "E2", "siguiente": "E3"},
        {"actual": "E3", "siguiente": "E4"},
    ]


def test_leer_csv_devuelve_tipos_nativos(tmp_path):
    df = pd.DataFrame(
        {
            "id": ["M1"],
            "capacidad_ud_h": [600.0],
            "vida_util_anos": [10],
        }
    )
    df.to_csv(tmp_path / "maquinas.csv", index=False)

    rows = load_data.leer_csv(tmp_path, "maquinas")

    assert type(rows[0]["id"]) is str
    assert type(rows[0]["capacidad_ud_h"]) is float
    assert type(rows[0]["vida_util_anos"]) is int


def test_dividir_sentencias_ignora_comentarios_y_lineas_vacias():
    texto = """
    // constraint de Linea
    CREATE CONSTRAINT a_unique IF NOT EXISTS FOR (n:A) REQUIRE n.id IS UNIQUE;

    // indice de fecha
    CREATE INDEX b_idx IF NOT EXISTS FOR (n:B) ON (n.fecha);
    """

    sentencias = load_data.dividir_sentencias(texto)

    assert len(sentencias) == 2
    assert sentencias[0].startswith("CREATE CONSTRAINT a_unique")
    assert sentencias[1].startswith("CREATE INDEX b_idx")
