# Escenario de la línea simulada

Línea de ensamblaje de placas electrónicas (PCBA — Printed Circuit Board
Assembly). Producto: placa de control para dispositivo IoT de complejidad
media. Estos son los valores de referencia que debe usar
`data-gen/generate.py` al crear los nodos `Maquina` y `MaquinaCandidata`.

**Parámetros generales**
- Horas de operación: 16 h/día (2 turnos), 5 días/semana
- Margen por placa terminada: 12 €
- Tasa de descuento (VAN): 10% anual (ya fijada en ARCHITECTURE.md)
- Histórico a generar: ~180 días

## Estaciones

| # | Estación | Máquina actual | Capacidad (placas/h) | OEE | Coste adquisición | Mantenimiento/año | Candidata de sustitución | Capacidad candidata | Coste candidata |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Inserción SMD | Pick & Place gama media | 600 | 0.85 | 180.000 € | 12.000 € | Pick & Place última generación | 900 (+50%) | 260.000 € |
| 2 | Soldadura (reflow) | Horno reflow estándar | 550 | 0.90 | 90.000 € | 6.000 € | Horno reflow de mayor capacidad | 700 (+27%) | 130.000 € |
| 3 | Inspección óptica (AOI) | AOI de gama básica | 400 | 0.75 | 70.000 € | 5.000 € | AOI con IA de nueva generación | 650 (+62%) | 150.000 € |
| 4 | Ensamblaje de carcasa | Cobot de ensamblaje | 500 | 0.88 | 45.000 € | 4.000 € | Cobot de mayor velocidad | 650 (+30%) | 65.000 € |
| 5 | Test funcional | Tester funcional simple | 450 | 0.92 | 60.000 € | 5.000 € | Tester paralelo multi-socket | 700 (+55%) | 95.000 € |

**Capacidad efectiva** (= capacidad × OEE) por estación, de menor a mayor:
- AOI: 400 × 0.75 = **300 placas/h** ← restricción de la línea
- Cobot ensamblaje: 500 × 0.88 = 440
- Reflow: 550 × 0.90 = 495
- Test funcional: 450 × 0.92 = 414
- Pick & Place: 600 × 0.85 = 510

La estación de AOI es la restricción real de la línea con estos números —
`detectar_cuello_botella` debería identificarla consistentemente, y es el
caso de uso natural para las preguntas de inversión ("¿si sustituyo el AOI,
cuánto mejora el throughput de toda la línea?").

## Consumo eléctrico (para completar `consumo_kwh` si se usa en el informe)

Pick & Place: 8 kWh · Reflow: 15 kWh · AOI: 3 kWh · Cobot: 2 kWh · Test: 4 kWh

## Vida útil (`vida_util_anos`)

Pick & Place: 10 · Reflow: 12 · AOI: 8 · Cobot: 10 · Test: 10
