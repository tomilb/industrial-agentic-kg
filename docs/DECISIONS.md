# Decisiones de diseño

Formato: fecha — decisión — alternativas consideradas — motivo. Una entrada
por decisión no trivial. No se borran entradas obsoletas, se añade una nueva
que referencia la anterior si cambia.

---

## 2026-07 — MCP en lugar de tool-use directo vía API

**Alternativas**: (a) Claude API con tool use clásico, (b) servidor MCP local.

**Decisión**: servidor MCP.

**Motivo**: permite conectar el mismo servidor tanto a Claude Desktop (demo
en vivo, sin código adicional) como a la API vía `mcp_servers` (demo
scriptada y reproducible desde el repo). El sobrecoste de montar el servidor
frente a tool-use directo es bajo con el SDK oficial de Python. Además es
la aplicación práctica directa del curso de MCP en curso.

---

## 2026-07 — Neo4j en lugar de base de datos relacional

**Alternativas**: PostgreSQL con tablas normalizadas, Neo4j.

**Decisión**: Neo4j.

**Motivo**: las consultas centrales del proyecto son de tipo "¿qué máquinas
pueden sustituir a esta?" y "¿qué estaciones preceden a esta otra?" —
relaciones de grafo naturales. Modelarlo en relacional exigiría varios JOINs
por consulta y ocultaría la topología de la línea, que es información de
primera clase para el caso de uso.

---

## 2026-07 — MVP sin pipeline MQTT ni simulación visual

**Alternativas**: (a) pipeline completo MQTT → ingesta → grafo (como en
CTAG), (b) simulación visual interactiva de la línea, (c) datos sintéticos
generados por script, cargados directamente al grafo.

**Decisión**: (c) para el MVP de 2-3 semanas; (a) y (b) quedan como
extensión futura ("Fase 2") documentada en el README.

**Motivo**: el objetivo prioritario del portfolio es demostrar razonamiento
financiero del agente sobre el grafo, no la infraestructura de ingesta (ya
demostrada en la experiencia previa en CTAG) ni la visualización. Cortar
esto reduce el riesgo de no llegar a un demo funcional en el plazo.

---

## 2026-07 — `data-gen/generate.py` escribe CSVs intermedios, no Neo4j directo

**Alternativas**: (a) CSVs intermedios en `data-gen/output/` que
`graph/load_data.py` lee y carga, (b) JSON único anidado, (c) `generate.py`
escribe directamente a Neo4j con el driver.

**Decisión**: (a) CSVs intermedios (`lineas`, `estaciones`, `maquinas`,
`maquinas_candidatas`, `registros_produccion`), uno por tipo de nodo del
esquema de `ARCHITECTURE.md`.

**Motivo**: mantiene la separación ya fijada en la estructura del repo
entre `data-gen/` (genera) y `graph/` (carga) — permite testear el
generador con `pytest` sobre estructuras en memoria/CSV sin tocar Neo4j
real, y deja un artefacto inspeccionable para el portfolio. Los CSVs no se
versionan (`data-gen/output/` en `.gitignore`): son regenerables de forma
determinista.

---

## 2026-07 — Modelo de OEE sintético para `RegistroProduccion`

**Alternativas**: (a) sortear `unidades`/`paradas_min`/`defectos` de forma
independiente por campo, (b) descomponer `oee_actual` en disponibilidad ×
rendimiento × calidad (modelo OEE estándar) con ruido gaussiano diario por
factor, derivando rendimiento base de cada estación a partir de constantes
globales de disponibilidad/calidad.

**Decisión**: (b). `AVAILABILIDAD_BASE = 0.96` y `CALIDAD_BASE = 0.98` son
constantes únicas para las 5 estaciones; `rendimiento_base` se deriva por
estación como `oee_actual / (AVAILABILIDAD_BASE * CALIDAD_BASE)`, así el
único dato de entrada por estación sigue siendo el `oee_actual` de
`docs/ESCENARIO.md`.

**Motivo**: sortear los tres factores de forma independiente en vez de
sumar/restar directamente sobre `unidades` da una serie temporal con ruido
realista y consistente con el desglose de OEE que un lector con
background industrial reconocerá, sin introducir tendencia/estacionalidad
que complicaría el MVP. El margen entre la capacidad efectiva del AOI
(~300 ud/h) y la siguiente estación más lenta (Cobot, ~440 ud/h) es lo
bastante amplio para que el cuello de botella sea consistente en el 100%
de los días generados, no solo en promedio (verificado con test).

`docs/ESCENARIO.md` no da `consumo_kwh`, `vida_util_anos` ni
`coste_mantenimiento_anual` propios para las `MaquinaCandidata` (solo por
categoría de máquina, o solo para la máquina actual). Se asume que la
candidata hereda esos tres valores de la máquina que sustituye, en vez de
inventar cifras nuevas — documentado también como comentario en
`data-gen/generate.py`.

---

## 2026-07 — `END_DATE` dinámica (`date.today()`) en vez de fecha fija

**Alternativas**: (a) `END_DATE` fija como constante (p.ej. 2026-06-30)
para que el CSV completo sea byte-a-byte idéntico entre ejecuciones en
cualquier día, (b) `END_DATE = date.today()`, recalculada en cada
ejecución.

**Decisión**: (b), a petición explícita del usuario tras revisar el plan.

**Motivo**: el histórico debe terminar "hoy" de verdad en cada
regeneración, no en una fecha congelada. El `SEED` de `numpy` se mantiene
fijo, así que los valores por registro siguen siendo reproducibles dentro
del mismo día de ejecución (mismo `--days`, mismo `--seed` ⇒ mismo CSV);
lo que ya no es estable entre días distintos es la ventana de fechas en
sí, lo cual es el comportamiento buscado.
