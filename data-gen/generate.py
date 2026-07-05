"""Genera el histórico sintético de producción descrito en docs/ESCENARIO.md.

Escribe CSVs en --output-dir (lineas, estaciones, maquinas,
maquinas_candidatas, registros_produccion) que graph/load_data.py carga a
Neo4j siguiendo el esquema de ARCHITECTURE.md.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# --- Configuración fija -------------------------------------------------

SEED = 42
# Fecha del sistema en el momento de ejecutar: el histórico siempre termina
# "hoy". El SEED se mantiene fijo para que, generando en el mismo día, los
# valores por registro sean reproducibles entre ejecuciones.
END_DATE = date.today()

MARGEN_PLACA_EUR = 12.0
HORAS_OPERACION_DIA = 16
DIAS_SEMANA = 5

# Constantes globales para descomponer oee_actual en disponibilidad x
# rendimiento x calidad (ver docs/DECISIONS.md). Elegidas para que
# performance_base = oee_actual / (AVAILABILIDAD_BASE * CALIDAD_BASE)
# quede < 1 para las 5 estaciones de ESCENARIO.md (la más alta, Test
# funcional con oee_actual=0.92, da ~0.978).
AVAILABILIDAD_BASE = 0.96
CALIDAD_BASE = 0.98

# Valores de referencia de docs/ESCENARIO.md. consumo_kwh y
# vida_util_anos no tienen un valor propio para la candidata en
# ESCENARIO.md (solo por categoría de máquina) -- se asume que la
# candidata hereda el consumo/vida útil de la máquina base de su misma
# categoría. coste_mantenimiento_anual de la candidata tampoco viene dado
# en ESCENARIO.md -- se asume igual al de la máquina que sustituye, por
# la misma razón. Ver docs/DECISIONS.md.
ESTACIONES: list[dict[str, Any]] = [
    {
        "id": "E1",
        "orden": 1,
        "nombre": "Inserción SMD",
        "maquina": {
            "id": "M1",
            "nombre": "Pick & Place gama media",
            "capacidad_ud_h": 600.0,
            "oee_actual": 0.85,
            "coste_adquisicion": 180_000.0,
            "coste_mantenimiento_anual": 12_000.0,
            "consumo_kwh": 8.0,
            "vida_util_anos": 10,
        },
        "candidatas": [
            {
                "id": "C1",
                "nombre": "Pick & Place última generación",
                "capacidad_ud_h": 900.0,
                "coste_adquisicion": 260_000.0,
                "coste_mantenimiento_anual": 12_000.0,
                "consumo_kwh": 8.0,
                "vida_util_anos": 10,
                "mejora_capacidad_pct": 50.0,
            },
        ],
    },
    {
        "id": "E2",
        "orden": 2,
        "nombre": "Soldadura (reflow)",
        "maquina": {
            "id": "M2",
            "nombre": "Horno reflow estándar",
            "capacidad_ud_h": 550.0,
            "oee_actual": 0.90,
            "coste_adquisicion": 90_000.0,
            "coste_mantenimiento_anual": 6_000.0,
            "consumo_kwh": 15.0,
            "vida_util_anos": 12,
        },
        "candidatas": [
            {
                "id": "C2",
                "nombre": "Horno reflow de mayor capacidad",
                "capacidad_ud_h": 700.0,
                "coste_adquisicion": 130_000.0,
                "coste_mantenimiento_anual": 6_000.0,
                "consumo_kwh": 15.0,
                "vida_util_anos": 12,
                "mejora_capacidad_pct": 27.0,
            },
        ],
    },
    {
        "id": "E3",
        "orden": 3,
        "nombre": "Inspección óptica (AOI)",
        "maquina": {
            "id": "M3",
            "nombre": "AOI de gama básica",
            "capacidad_ud_h": 400.0,
            "oee_actual": 0.75,
            "coste_adquisicion": 70_000.0,
            "coste_mantenimiento_anual": 5_000.0,
            "consumo_kwh": 3.0,
            "vida_util_anos": 8,
        },
        "candidatas": [
            {
                "id": "C3",
                "nombre": "AOI con IA de nueva generación",
                "capacidad_ud_h": 650.0,
                "coste_adquisicion": 150_000.0,
                "coste_mantenimiento_anual": 5_000.0,
                "consumo_kwh": 3.0,
                "vida_util_anos": 8,
                "mejora_capacidad_pct": 62.0,
            },
        ],
    },
    {
        "id": "E4",
        "orden": 4,
        "nombre": "Ensamblaje de carcasa",
        "maquina": {
            "id": "M4",
            "nombre": "Cobot de ensamblaje",
            "capacidad_ud_h": 500.0,
            "oee_actual": 0.88,
            "coste_adquisicion": 45_000.0,
            "coste_mantenimiento_anual": 4_000.0,
            "consumo_kwh": 2.0,
            "vida_util_anos": 10,
        },
        "candidatas": [
            {
                "id": "C4",
                "nombre": "Cobot de mayor velocidad",
                "capacidad_ud_h": 650.0,
                "coste_adquisicion": 65_000.0,
                "coste_mantenimiento_anual": 4_000.0,
                "consumo_kwh": 2.0,
                "vida_util_anos": 10,
                "mejora_capacidad_pct": 30.0,
            },
        ],
    },
    {
        "id": "E5",
        "orden": 5,
        "nombre": "Test funcional",
        "maquina": {
            "id": "M5",
            "nombre": "Tester funcional simple",
            "capacidad_ud_h": 450.0,
            "oee_actual": 0.92,
            "coste_adquisicion": 60_000.0,
            "coste_mantenimiento_anual": 5_000.0,
            "consumo_kwh": 4.0,
            "vida_util_anos": 10,
        },
        "candidatas": [
            {
                "id": "C5",
                "nombre": "Tester paralelo multi-socket",
                "capacidad_ud_h": 700.0,
                "coste_adquisicion": 95_000.0,
                "coste_mantenimiento_anual": 5_000.0,
                "consumo_kwh": 4.0,
                "vida_util_anos": 10,
                "mejora_capacidad_pct": 55.0,
            },
        ],
    },
]

LINEA_ID = "L1"
LINEA_NOMBRE = "Línea de ensamblaje PCBA"


# --- Nodos estáticos ------------------------------------------------------


def construir_linea() -> dict[str, Any]:
    return {"id": LINEA_ID, "nombre": LINEA_NOMBRE}


def construir_estaciones_y_maquinas(
    estaciones_cfg: list[dict[str, Any]],
) -> tuple[list[dict], list[dict], list[dict]]:
    """A partir de ESTACIONES, arma las filas de estaciones/maquinas/candidatas."""
    estaciones_rows = []
    maquinas_rows = []
    candidatas_rows = []

    for estacion in estaciones_cfg:
        estaciones_rows.append(
            {
                "id": estacion["id"],
                "linea_id": LINEA_ID,
                "nombre": estacion["nombre"],
                "orden": estacion["orden"],
            }
        )

        maquina = estacion["maquina"]
        maquinas_rows.append({**maquina, "estacion_id": estacion["id"]})

        for candidata in estacion["candidatas"]:
            candidatas_rows.append({**candidata, "maquina_id": maquina["id"]})

    return estaciones_rows, maquinas_rows, candidatas_rows


# --- Fechas laborables ------------------------------------------------------


def dias_laborables(end_date: date, n_dias: int) -> list[date]:
    """Días lu-vi en la ventana [end_date - (n_dias-1), end_date]."""
    start_date = end_date - timedelta(days=n_dias - 1)
    dias = []
    dia = start_date
    while dia <= end_date:
        if dia.weekday() < DIAS_SEMANA:  # 0=lunes ... 4=viernes
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


# --- Modelo de RegistroProduccion -------------------------------------------


def generar_registro(
    maquina_cfg: dict[str, Any], fecha: date, rng: np.random.Generator
) -> dict[str, Any]:
    """Genera un RegistroProduccion diario a partir de un modelo de OEE
    estándar (disponibilidad x rendimiento x calidad) derivado de
    oee_actual, con ruido gaussiano diario independiente por factor.
    """
    performance_base = maquina_cfg["oee_actual"] / (AVAILABILIDAD_BASE * CALIDAD_BASE)

    disponibilidad = float(np.clip(rng.normal(AVAILABILIDAD_BASE, 0.02), 0.0, 1.0))
    rendimiento = float(np.clip(rng.normal(performance_base, 0.025), 0.0, 1.0))
    calidad = float(np.clip(rng.normal(CALIDAD_BASE, 0.01), 0.0, 1.0))

    tiempo_disponible_min = HORAS_OPERACION_DIA * 60
    paradas_min = tiempo_disponible_min * (1 - disponibilidad)
    tiempo_operativo_s = (tiempo_disponible_min - paradas_min) * 60

    ciclo_ideal_s = 3600 / maquina_cfg["capacidad_ud_h"]
    unidades_teoricas = (tiempo_operativo_s / ciclo_ideal_s) * rendimiento

    defectos = round(unidades_teoricas * (1 - calidad))
    unidades = round(unidades_teoricas - defectos)
    tiempo_ciclo_s = tiempo_operativo_s / unidades_teoricas

    return {
        "maquina_id": maquina_cfg["id"],
        "fecha": fecha.isoformat(),
        "unidades": int(unidades),
        "tiempo_ciclo_s": round(tiempo_ciclo_s, 2),
        "paradas_min": round(paradas_min, 1),
        "defectos": int(defectos),
    }


def generar_registros_produccion(
    maquinas_rows: list[dict[str, Any]], fechas: list[date], seed: int
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    registros = []
    for fecha in fechas:
        for maquina in maquinas_rows:
            registros.append(generar_registro(maquina, fecha, rng))
    return registros


# --- Orquestación -----------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations", type=int, default=len(ESTACIONES))
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "output",
    )
    return parser.parse_args(argv)


def generar_dataset(n_estaciones: int, n_dias: int, seed: int) -> dict[str, list[dict[str, Any]]]:
    if not 1 <= n_estaciones <= len(ESTACIONES):
        raise ValueError(
            f"--stations debe estar entre 1 y {len(ESTACIONES)}, recibido {n_estaciones}"
        )

    estaciones_cfg = ESTACIONES[:n_estaciones]
    estaciones_rows, maquinas_rows, candidatas_rows = construir_estaciones_y_maquinas(
        estaciones_cfg
    )
    fechas = dias_laborables(END_DATE, n_dias)
    registros_rows = generar_registros_produccion(maquinas_rows, fechas, seed)

    return {
        "lineas": [construir_linea()],
        "estaciones": estaciones_rows,
        "maquinas": maquinas_rows,
        "maquinas_candidatas": candidatas_rows,
        "registros_produccion": registros_rows,
    }


def escribir_csvs(dataset: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for nombre, filas in dataset.items():
        pd.DataFrame(filas).to_csv(output_dir / f"{nombre}.csv", index=False)


def imprimir_resumen(dataset: dict[str, list[dict[str, Any]]]) -> None:
    registros = pd.DataFrame(dataset["registros_produccion"])
    maquinas = pd.DataFrame(dataset["maquinas"])

    fechas = registros["fecha"]
    print(f"Registros de producción: {len(registros)}")
    print(f"Rango de fechas: {fechas.min()} .. {fechas.max()}")

    capacidad_efectiva = maquinas.set_index("id").apply(
        lambda m: m["capacidad_ud_h"] * m["oee_actual"], axis=1
    )
    restriccion_id = capacidad_efectiva.idxmin()
    restriccion_nombre = maquinas.set_index("id").loc[restriccion_id, "nombre"]
    print(
        f"Estación con menor capacidad efectiva (restricción): "
        f"{restriccion_id} - {restriccion_nombre} "
        f"({capacidad_efectiva.min():.0f} ud/h)"
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    dataset = generar_dataset(args.stations, args.days, args.seed)
    escribir_csvs(dataset, args.output_dir)
    imprimir_resumen(dataset)


if __name__ == "__main__":
    main()
