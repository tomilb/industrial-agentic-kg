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
   Servidor MCP (5 tools)
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
| `anos_en_servicio` | int | solo en `Maquina` — años que esa unidad concreta lleva instalada, no una característica del modelo (ver `docs/ESCENARIO.md`) |

**RegistroProduccion**
| Propiedad | Tipo | Descripción |
|---|---|---|
| `fecha` | date | |
| `unidades` | int | producidas ese turno/día |
| `tiempo_ciclo_s` | float | promedio |
| `paradas_min` | float | tiempo parado |
| `defectos` | int | |

## Servidor MCP — 5 tools

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
- **Entrada**: `linea_id` (opcional; por defecto la única `Linea` del grafo),
  `desde`, `hasta` (fechas ISO `YYYY-MM-DD`) — delimitan el periodo usado
  para las métricas empíricas.
- **Salida**: por estación — `estacion_id`, `estacion_nombre`, `maquina_id`,
  `capacidad_ud_h`, `oee_actual`, `capacidad_efectiva` (= `capacidad_ud_h` ×
  `oee_del_periodo`, donde `oee_del_periodo` es el `oee` **empírico** de esa
  estación en `[desde, hasta]`; si no hay `RegistroProduccion` en ese rango
  para la estación, se usa `oee_actual` **estático** como fallback solo para
  esa estación), `oee` (empírico: media de
  `unidades / (capacidad_ud_h × HORAS_OPERACION_DIA)` sobre los
  `RegistroProduccion` del periodo; `None` si no hay registros en ese rango
  para la estación), `utilizacion_pct` (empírico: disponibilidad media,
  `(tiempo_disponible - paradas_min) / tiempo_disponible × 100`, sobre el
  mismo periodo; `None` si no hay registros), `fuente_oee`
  (`"empirico"` | `"estatico_sin_datos"` — de dónde salió el oee usado para
  calcular `capacidad_efectiva` de esa estación), `es_restriccion` (bool).
- **Lógica**: la estación con menor `capacidad_efectiva` marca el throughput
  máximo de la línea (teoría de restricciones) — es la que se marca
  `es_restriccion: true` (o varias, en caso de empate exacto). El oee usado
  para `capacidad_efectiva` es el **empírico** del periodo cuando hay datos,
  y el **estático** (`oee_actual`) como fallback cuando no los hay — nunca
  `capacidad_ud_h` nominal sola. `HORAS_OPERACION_DIA` (16, ver
  `docs/ESCENARIO.md`) es una constante fija del servidor MCP, no un
  parámetro de esta tool, porque el histórico ya se generó con ese valor
  fijo.

### 4. `generar_informe`
- **Entrada**: `periodo` (`"mensual"` | `"trimestral"`), `fecha_referencia`
  (ISO `YYYY-MM-DD`, por defecto hoy). `linea_id` no se expone como
  parámetro (MVP de una sola línea; se resuelve igual que en las demás
  tools).
- **Salida**: `{"ruta": str}` al documento generado en
  `reports/output/informe_<periodo>_<fecha_referencia>.docx`, o el
  contrato de error común si falla.
- **Periodo**: ventana móvil que termina en `fecha_referencia` —
  `"mensual"` = 30 días, `"trimestral"` = 91 días (no meses/trimestres de
  calendario). El periodo anterior de igual duración (inmediatamente
  anterior, sin solape) se calcula para la sección de evolución del
  cuello de botella.
- **Implementación**: el documento se genera **desde cero** con
  `python-docx` (no hay plantilla `.docx` — no aplica el punto de
  `docs/DECISIONS.md` sobre esto). Usa el logo ya rasterizado en
  `skills/informe-corporativo/assets/logo.png` (sin conversión SVG→PNG en
  runtime) y 3 gráficas generadas con `matplotlib`: producción diaria
  total de la línea, comparativa de OEE empírico por estación, y
  evolución de la `capacidad_efectiva` de la restricción entre el periodo
  actual y el anterior. Encabezados con estilos nativos de Word (Heading
  1/2), no negrita simulando títulos. Las **recomendaciones** se derivan
  de datos reales de `detectar_cuello_botella` + `consultar_grafo` +
  `calcular_financiero` (nunca texto de plantilla fijo) — ver
  `docs/DECISIONS.md` para el detalle de cómo se calculan.
- **Maquetación visual** (marca "NEXATRON Electronics", navy `#0B2545` /
  teal `#12C2A9`, ver `skills/informe-corporativo/assets/logo.svg`):
  - Portada: bloque de color navy ocupando el tercio superior de la
    primera página (tabla de 1 celda con sombreado, no texto suelto),
    con el logo y el título del informe en blanco superpuestos dentro.
  - Antes de la tabla de KPIs: 3 tarjetas en línea (número grande +
    etiqueta) con las cifras clave — unidades totales, OEE medio,
    estación restricción — separadas de la tabla detallada por una
    línea divisoria sutil y espaciado adicional.
  - Tabla de KPIs por estación: cabecera con fondo navy y texto blanco
    en negrita, en vez del estilo por defecto de Word.
  - Pie de página en todas las páginas: "NEXATRON Electronics · Línea
    {linea_id} · Página {n}", con el número de página como campo nativo
    de Word (`PAGE`), no texto fijo.
  - Las 3 gráficas comparten estilo: paleta navy/teal (nunca la paleta
    por defecto de matplotlib), sin gridlines ni marco superior/derecho,
    y etiquetas de valor sobre cada barra/punto — excepto en la serie
    temporal de producción diaria, donde sería ilegible.
  - Todos los números del documento (resumen, tarjetas, tabla,
    diagnóstico, recomendaciones, gráficas) usan formato español: punto
    como separador de miles, coma como separador decimal (p.ej.
    "2.234.516", "16.019%").

### 5. `consultar_manual_tecnico`
- **Entrada**: `maquina_id` (str, `Maquina` o `MaquinaCandidata`),
  `pregunta` (str, lenguaje natural)
- **Salida**: `{"maquina_id": str, "chunks": [{"seccion": str, "texto": str,
  "score": float}, ...]}`, o el contrato de error común si no hay manual
  cargado para esa máquina.
- **Esquema**: nodos `(:ManualChunk {id, maquina_id, seccion, texto,
  embedding})`, relacionados `(:Maquina)-[:TIENE_MANUAL]->(:ManualChunk)`
  o `(:MaquinaCandidata)-[:TIENE_MANUAL]->(:ManualChunk)` según
  corresponda. Cargados por `graph/load_manuals.py` (separado de
  `load_data.py`), idempotente vía `MERGE` sobre un id determinista
  (`{maquina_id}-{slug(seccion)}`).
- **Implementación**: RAG con el **índice vectorial nativo de Neo4j**
  (`db.index.vector.queryNodes`), sin base de datos vectorial aparte.
  Embeddings con `sentence-transformers`
  (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones, local — sin
  API key ni red tras la primera descarga) — el mismo modelo se usa para
  indexar los manuales y para embeber la pregunta en tiempo de consulta.
  Chunking por sección (cada `##` de `manuales/*.md` es un chunk), no por
  documento completo — ver `docs/DECISIONS.md` para el razonamiento. Se
  piden más candidatos de los que hacen falta al índice vectorial
  (`db.index.vector.queryNodes` no filtra por `maquina_id`) y se filtra
  después en Cypher, para no perder chunks relevantes de la máquina
  pedida que no entrarían en un top-k global pequeño.
- **Diagnóstico de causa raíz**: para preguntas de causa raíz de un
  defecto o incidencia (no solo "qué mantenimiento lleva X"), el
  docstring de la tool indica al agente que conviene consultar también
  el manual de la estación **inmediatamente anterior** en la línea, no
  solo la estación donde se observa el síntoma — muchas incidencias se
  documentan como manifestándose aguas abajo de su causa real. El propio
  docstring sugiere usar `consultar_grafo(topologia_linea)` primero para
  identificar esa estación anterior, y hacer una segunda llamada a
  `consultar_manual_tecnico` con su `maquina_id`. Es una indicación de
  uso en el texto que lee el agente, no un cambio de contrato: la entrada/
  salida y el filtro `WHERE node.maquina_id` de la tool no cambian.

## Flujo de una pregunta típica

1. Usuario: *"¿Si sustituyo la máquina M3 por la candidata C1, cuándo recupero la inversión?"*
2. Agente llama `consultar_grafo(candidatos_sustitucion, {maquina_id: M3})` → obtiene specs de M3 y C1
3. Agente llama `calcular_financiero(...)` con los datos anteriores
4. Agente redacta la respuesta citando las cifras devueltas por la tool, no inventadas
