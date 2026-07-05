import generate
import pandas as pd
import pytest

SEED = 123
N_DIAS = 180


@pytest.fixture(scope="module")
def dataset():
    return generate.generar_dataset(n_estaciones=5, n_dias=N_DIAS, seed=SEED)


def test_registros_por_maquina_coincide_con_dias_laborables(dataset):
    fechas_esperadas = generate.dias_laborables(generate.END_DATE, N_DIAS)
    registros = pd.DataFrame(dataset["registros_produccion"])
    conteo_por_maquina = registros.groupby("maquina_id").size()

    assert set(conteo_por_maquina.index) == {"M1", "M2", "M3", "M4", "M5"}
    assert (conteo_por_maquina == len(fechas_esperadas)).all()


def test_oee_medio_implicito_cerca_de_oee_actual(dataset):
    registros = pd.DataFrame(dataset["registros_produccion"])
    maquinas = pd.DataFrame(dataset["maquinas"]).set_index("id")

    for maquina_id, grupo in registros.groupby("maquina_id"):
        capacidad = maquinas.loc[maquina_id, "capacidad_ud_h"]
        oee_actual = maquinas.loc[maquina_id, "oee_actual"]
        oee_medio_implicito = (
            grupo["unidades"] / (capacidad * generate.HORAS_OPERACION_DIA)
        ).mean()
        assert oee_medio_implicito == pytest.approx(oee_actual, abs=0.03)


def test_aoi_es_la_estacion_con_menor_capacidad_efectiva(dataset):
    registros = pd.DataFrame(dataset["registros_produccion"])
    maquinas = pd.DataFrame(dataset["maquinas"]).set_index("id")

    capacidad_efectiva_media = (
        registros.groupby("maquina_id")["unidades"].mean() / generate.HORAS_OPERACION_DIA
    )
    estacion_restriccion = capacidad_efectiva_media.idxmin()

    assert maquinas.loc[estacion_restriccion, "nombre"] == "AOI de gama básica"


def test_generacion_es_reproducible_con_mismo_seed(dataset):
    otro = generate.generar_dataset(n_estaciones=5, n_dias=N_DIAS, seed=SEED)
    assert dataset["registros_produccion"] == otro["registros_produccion"]


@pytest.mark.parametrize("n_estaciones", [0, 99])
def test_stations_fuera_de_rango_lanza_valueerror(n_estaciones):
    with pytest.raises(ValueError):
        generate.generar_dataset(n_estaciones=n_estaciones, n_dias=10, seed=SEED)
