# Arquitectura — Industrial Agentic Knowledge Graph

## Visión general

```
Datos sintéticos (pandas)
        │
        ▼
   graph/load_data.py
        │
        ▼
   Neo4j (knowledge graph de planta)
        │
        ▼
   Servidor MCP (4 tools)
        │
        ▼
Agente (Claude Desktop / API) ── informe (Skills)
```

MVP de alcance reducido: no hay pipeline MQTT en vivo ni simulación visual
interactiva (ver `docs/DECISIONS.md`). Los datos de producción son sintéticos
pero generados con un cuello de botella deliberado, para que las respuestas
del agente sobre optimización tengan una base real que verificar.

## Esquema del grafo (Neo4j)

```
(:Linea)-[:TIENE_ESTACION]->(:Estacion)-[:OPERA]->(:Maquina)
(:Estacion)-[:PRECEDE_A]->(:Estacion)
(:Maquina)-[:PUEDE_SUSTITUIRSE_POR]->(:MaquinaCandidata)
(:Maquina)-[:REGISTRA]->(:RegistroProduccion)
```

### Propiedades por nodo

**Maquina / MaquinaCandidata**
| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | string | identificador único |
| `nombre` | string | |
| `coste_adquisicion` | float | € |
| `capacidad_ud_h` | float | unidades/hora nominal |
| `oee_actual` | float | 0-1, solo en `Maquina` |
| `coste_mantenimiento_anual` | float | € |
| `consumo_kwh` | float | por hora de operación |
| `vida_util_anos` | int | |
| `mejora_capacidad_pct` | float | solo en `MaquinaCandidata`, vs. la máquina que sustituye |

**RegistroProduccion**
| Propiedad | Tipo | Descripción |
|---|---|---|
| `fecha` | date | |
| `unidades` | int | producidas ese turno/día |
| `tiempo_ciclo_s` | float | promedio |
| `paradas_min` | float | tiempo parado |
| `defectos` | int | |

## Servidor MCP — 4 tools

Todas las tools devuelven JSON validado con Pydantic. Contrato de error común:
`{"error": str, "detalle": str | None}`.

### 1. `consultar_grafo`
- **Entrada**: `pregunta_estructurada` (enum: `specs_maquina`, `topologia_linea`,
  `candidatos_sustitucion`) + `params` (dict, p.ej. `{"maquina_id": "..."}`)
- **Salida**: nodos/propiedades relevantes en JSON
- **Nota**: exponer funciones semánticas, no Cypher libre — reduce el riesgo
  de que el agente construya una query incorrecta o poco eficiente.

### 2. `calcular_financiero`
- **Entrada**: `coste_inversion`, `capacidad_actual_ud_h`, `capacidad_nueva_ud_h`,
  `margen_por_unidad`, `horas_operacion_dia`, `horizonte_anos`
- **Salida**: `payback_meses`, `roi_pct`, `van` (con una tasa de descuento
  fija razonable, documentada aquí: **10% anual**)
- **Fórmulas**:
  - `ganancia_diaria = (capacidad_nueva - capacidad_actual) * margen_por_unidad * horas_operacion_dia`
  - `payback_meses = coste_inversion / (ganancia_diaria * 30)`
  - `roi_pct = ((ganancia_diaria * 365 * horizonte_anos) - coste_inversion) / coste_inversion * 100`
  - VAN con flujo anual constante y tasa de descuento del 10%

### 3. `detectar_cuello_botella`
- **Entrada**: `linea_id`, `periodo` (rango de fechas)
- **Salida**: por estación, `utilizacion_pct`, `oee`, `es_restriccion` (bool)
- **Lógica**: la estación con menor `capacidad_efectiva` (capacidad nominal ×
  OEE) marca el throughput máximo de la línea (teoría de restricciones) — es
  la que se marca `es_restriccion: true`.

### 4. `generar_informe`
- **Entrada**: `periodo` (mensual/trimestral), `linea_id`
- **Salida**: ruta al documento generado
- **Implementación**: agrega los datos de producción del periodo + resultados
  de `detectar_cuello_botella`, y usa la plantilla corporativa (`reports/`) vía
  Skills para producir el docx/PDF final con gráficas.

## Flujo de una pregunta típica

1. Usuario: *"¿Si sustituyo la máquina M3 por la candidata C1, cuándo recupero la inversión?"*
2. Agente llama `consultar_grafo(candidatos_sustitucion, {maquina_id: M3})` → obtiene specs de M3 y C1
3. Agente llama `calcular_financiero(...)` con los datos anteriores
4. Agente redacta la respuesta citando las cifras devueltas por la tool, no inventadas
