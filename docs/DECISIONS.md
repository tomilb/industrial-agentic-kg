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

---

## 2026-07 — `mcp-server/server.py`: primera tool (`consultar_grafo`)

**Alternativas para `pregunta_estructurada`**: (a) tipar el parámetro como
`Literal["specs_maquina", "topologia_linea", "candidatos_sustitucion"]`,
(b) tipar como `str` y validar el enum a mano dentro de la función.

**Decisión**: (b).

**Motivo**: comprobado en el propio SDK
(`mcp/server/fastmcp/tools/base.py`, método `Tool.run`) que si la
validación de argumentos de FastMCP rechaza un valor (p.ej. por no
cumplir un `Literal`), la excepción se envuelve en un `ToolError` y se
devuelve como error de protocolo MCP (`isError: true`) — no como el JSON
`{"error": str, "detalle": str | None}` que exige `CLAUDE.md`. Tipando
`str` y validando el enum dentro de `_ejecutar_consulta`, todo fallo de
dominio (enum inválido, `maquina_id` inexistente, Neo4j caído) pasa
siempre por nuestro propio contrato de error. Los fallos de *tipo* de
argumento (p.ej. pasar un número) se dejan en manos del protocolo MCP —
reimplementar esa capa no aporta nada al MVP.

**Alternativas para la conexión a Neo4j**: (a) driver global creado de
forma perezosa (primera tool call), (b) driver global creado al importar
el módulo, (c) `lifespan` de FastMCP (inyección vía `Context`).

**Decisión**: (a).

**Motivo**: `GraphDatabase.driver(...)` no conecta de forma eager, así
que crearlo al importar (b) sería seguro para producción pero acopla los
tests a tener `NEO4J_*` en el entorno — con (a), importar `server.py` en
`mcp-server/tests/test_server.py` nunca dispara `get_driver()`, y las
funciones de consulta se testean pasándoles un driver falso. Se descarta
`lifespan` (c) por ser la solución pensada para servidores concurrentes
multi-cliente; este servidor es stdio de un solo cliente (Claude
Desktop), así que esa capa de indirección no se justifica.

`get_driver()` se duplica en `mcp-server/server.py` en vez de importarse
desde `graph/load_data.py`: Claude Desktop lanza el servidor como
subproceso con ruta absoluta y su propio `cwd` (`docs/MCP_CLIENT_CONFIG.md`),
así que depender de un import cruzado a `graph/` obligaría a manipular
`sys.path` de forma frágil para una función de 5 líneas.

`topologia_linea` reconstruye el orden de las estaciones recorriendo
`PRECEDE_A` en Python (`_ordenar_estaciones_por_cadena`), no leyendo una
propiedad `orden` — continúa la misma decisión ya tomada al cargar el
grafo (esa propiedad nunca se persistió).

---

## 2026-07 — `calcular_financiero`: tratamiento de 3 casos límite

**Caso `capacidad_nueva_ud_h <= capacidad_actual_ud_h`** (la inversión no
mejora o empeora): **no se trata como error**. `ganancia_diaria` sale ≤ 0;
`payback_meses` se fija a `None` (evita dividir por cero o devolver un
mes negativo sin sentido), mientras que `roi_pct` y `van` se calculan con
la fórmula normal y salen ≤ 0 de forma natural (p.ej. `roi_pct == -100.0`
exacto cuando `ganancia_diaria == 0`, porque el único flujo es perder
`coste_inversion`). Es un resultado financiero legítimo (mala inversión o
comparación de candidatas), no un fallo de la tool.

**Caso `margen_por_unidad` ≤ 0**: a diferencia del anterior, **sí es un
error de validación** — no representa un escenario de negocio real para
este dominio y provocaría división por cero/signos sin sentido. Se valida
con Pydantic (`CalcularFinancieroInput`, `Field(gt=0)`), igual que
`coste_inversion` (`gt=0`, evita dividir por cero en `roi_pct`) y
`horas_operacion_dia`/`horizonte_anos` (`gt=0`). Un fallo de validación se
captura como `pydantic.ValidationError` y se traduce al contrato de error
común (`{"error": "Parámetros de entrada inválidos", "detalle": str(e)}`).
`capacidad_actual_ud_h`/`capacidad_nueva_ud_h` solo exigen `ge=0` — su
comparación relativa es el caso anterior, válido.

**Caso payback más allá de `horizonte_anos`**: se devuelve el
`payback_meses` real sin recortarlo ni sustituirlo (p.ej. 416.7 con un
horizonte de 12 meses) — es matemáticamente correcto y comparable
directamente contra `horizonte_anos * 12` por quien hizo la petición
(ya tiene ese dato). No se añade un campo nuevo tipo
`recuperada_dentro_horizonte` al contrato de `ARCHITECTURE.md`: no
aportaría información que el `payback_meses` real no dé ya, y el único
caso realmente "engañoso" (división por cero) ya está cubierto por el
`None` del primer caso.

---

## 2026-07 — `detectar_cuello_botella`: capacidad_efectiva estática vs oee/utilización empíricos

**Motivo del cambio**: probando a mano en Claude Desktop, decidir
`es_restriccion` comparando `capacidad_ud_h` nominal directamente dio una
respuesta casualmente correcta con los datos actuales, pero no robusta —
una estación con capacidad nominal alta y OEE bajo puede seguir siendo la
restricción real de la línea. Verificado también en el sanity check final
contra Neo4j real: AOI sale con `capacidad_efectiva=300.0` y
`es_restriccion=true`, exactamente como fija `docs/ESCENARIO.md`.

**Decisión**: `capacidad_efectiva = capacidad_ud_h × oee_actual` (ambas
propiedades **estáticas** de `Maquina`) es la única fuente de verdad para
`es_restriccion` — nunca `capacidad_ud_h` nominal sola. Es la estación con
`capacidad_efectiva` mínima de la línea; en caso de empate exacto, se
marcan todas las empatadas (comparación por igualdad, no hay deriva de
coma flotante porque es una multiplicación directa de dos valores
almacenados, igual para cada fila). `capacidad_efectiva` se expone en la
salida de cada estación — no solo la restricción — para que
`calcular_financiero` pueda recibir el throughput de línea correcto
antes/después de un cambio propuesto (ver también la nota añadida al
docstring de `calcular_financiero`).

`oee` y `utilizacion_pct`, en cambio, son **empíricos**: se calculan
agregando los `RegistroProduccion` reales dentro de `[desde, hasta]`
(`oee` = media de `unidades / (capacidad_ud_h × HORAS_OPERACION_DIA)`,
mismo cálculo que ya usa `data-gen/tests/test_generate.py`;
`utilizacion_pct` = disponibilidad media,
`(tiempo_disponible - paradas_min) / tiempo_disponible × 100`). Si no hay
registros en el periodo para una estación, ambos quedan en `None` — no es
un error, es ausencia de datos históricos, y no impide calcular
`capacidad_efectiva`/`es_restriccion` (que no dependen del periodo).

`HORAS_OPERACION_DIA = 16` es una constante fija del servidor (ver
`docs/ESCENARIO.md`), no un parámetro de la tool: el histórico ya se
generó con ese valor fijo, así que exponerlo como parámetro permitiría
pedir un cálculo inconsistente con los datos reales.

`_resolver_linea_id` se extrajo como helper compartido con
`_consultar_topologia_linea` (mismo "si no viene linea_id, usar la única
Linea del grafo") — ya se repetía dos veces, tercera vez habría sido
duplicación clara.

---

## 2026-07 — `detectar_cuello_botella`: capacidad_efectiva pasa de estática a empírica-con-fallback

**Cambio sobre la decisión anterior** (capacidad_efectiva = capacidad_ud_h
× `oee_actual` estático): el usuario pidió un paso más — usar el `oee`
**empírico** del periodo (ya calculado en la misma tool) para
`capacidad_efectiva`, porque una estación puede tener buena ficha técnica
pero rendir peor en la práctica, y detectar eso es justo el propósito de
esta tool.

**Decisión**: `capacidad_efectiva = capacidad_ud_h × oee_del_periodo`,
donde `oee_del_periodo` es el `oee` empírico si la estación tiene
`RegistroProduccion` en `[desde, hasta]`; si no los tiene (`oee` empírico
es `None`), cae a `oee_actual` (ficha estática) **solo para esa
estación** — nunca se deja de poder calcular `capacidad_efectiva` por
falta de datos históricos. Se añade `fuente_oee`
(`"empirico"` | `"estatico_sin_datos"`) por estación para que quede
trazable cuál de las dos fuentes se usó, en vez de mezclar datos reales y
de ficha sin distinguirlos. Lógica extraída a un helper puro
`_resolver_oee_para_capacidad(oee_empirico, oee_actual) -> (oee, fuente)`.

**Verificado**: un test de regresión construye dos estaciones donde el
criterio estático y el empírico dan resultados **distintos** sobre cuál es
la restricción (ficha buena + rendimiento real malo vs. ficha peor pero
rendimiento real acorde) — confirma que la tool usa el empírico, no el
estático, cuando ambos discrepan. Contra el Neo4j real (periodo
2026-01-01/2026-03-31) las 5 estaciones tienen `fuente_oee="empirico"` y
AOI sigue siendo la restricción con estos datos — el ruido del generador
no es tan grande como para invertir el resultado con el dataset real; el
caso que sí lo invierte es un fixture de test deliberado, no el dataset
del proyecto.

---

## 2026-07 — `generar_informe`: sin dependencia de rasterización SVG

**Alternativas para el logo**: (a) rasterizar `assets/logo.svg` a PNG en
runtime con `cairosvg` (cacheando el resultado en `assets/`), (b) usar un
PNG ya generado y versionado junto al SVG, sin ninguna librería de
conversión.

**Decisión**: (b). `cairosvg` requiere la librería nativa `libcairo-2.dll`
(vía `cairocffi`), confirmada como no disponible en este Windows sin
instalar GTK3 runtime a nivel de sistema (smoke test real falló con
`OSError: no library called "cairo-2" was found`). Se descartó también
`resvg-py` (alternativa sin dependencia nativa, wheel verificado
disponible para este Python/Windows) porque el usuario ya tenía
`assets/logo.png` (480×120) generado a mano a partir del SVG de marca.
`cairosvg`/`cairocffi` se instalaron y desinstalaron del `.venv`;
`matplotlib` sí quedó como dependencia real (para las 3 gráficas) y se
añadió a `requirements.txt`. Si el logo de marca cambia en el futuro, el
PNG hay que regenerarlo a mano — no hay pipeline automático.

**Periodo como ventana móvil, no calendario**: `"mensual"` = 30 días,
`"trimestral"` = 91 días, terminando en `fecha_referencia` — no meses/
trimestres de calendario. Motivo: evita casos borde de "mes parcial" (qué
hacer si `fecha_referencia` cae a mitad de mes) y es coherente con cómo
`data-gen`/las demás tools ya tratan "periodo" como rango de fechas
explícito, no como unidad de calendario. El periodo anterior para la
comparación de cuello de botella es la ventana contigua inmediatamente
anterior, misma duración, sin solape.

**Cómo se generan las recomendaciones** (nunca texto de plantilla fijo):
1. Identificación de la restricción (`capacidad_efectiva` mínima, ya
   calculada por `detectar_cuello_botella`) + el % de brecha real con la
   segunda estación más lenta.
2. Comparación con el periodo anterior (misma duración, inmediatamente
   anterior): si cambió la estación restricción se cita cuál era/es con
   ambas capacidades; si es la misma, se cita el delta % real de mejora o
   empeoramiento.
3. Si la máquina restricción tiene `MaquinaCandidata`, se llama a
   `_calcular_financiero` (la función interna) con
   `capacidad_actual_ud_h` = `capacidad_efectiva` de la restricción y
   `capacidad_nueva_ud_h` = `min(candidata.capacidad_ud_h × oee_usado,
   capacidad_efectiva de la segunda estación más lenta)` — el `min` es
   necesario porque sustituir la restricción no puede mejorar la línea
   más allá de lo que permita la siguiente estación más lenta (mismo
   principio que la nota ya añadida al docstring de `calcular_financiero`).
   `oee_usado = restriccion.capacidad_efectiva / restriccion.capacidad_ud_h`
   porque `MaquinaCandidata` no tiene su propio `oee` en el esquema — se
   asume que rendiría con el mismo ratio que la máquina actual.
   `margen_por_unidad` usa la constante fija `MARGEN_POR_UNIDAD_EUR = 12.0`
   (ver `docs/ESCENARIO.md`) y `horizonte_anos = 3` (fijo, coherente con
   `docs/EVAL_QUESTIONS.md`), porque no hay forma de derivarlos del grafo.
   Si no hay candidata, y el oee empírico está ≥3 puntos por debajo de la
   ficha, se recomienda revisar mantenimiento en vez de sustitución.

**Verificado contra Neo4j real** (trimestral, `fecha_referencia` de hoy):
AOI sale como restricción con `capacidad_efectiva≈297` ud/h, la
recomendación cita la sustitución real por su candidata con payback/ROI
calculados, y la tendencia frente al periodo anterior ("empeorado un 1%")
es un dato genuino, no una plantilla. Un bug real apareció en esta
verificación: el driver de Neo4j devuelve `RegistroProduccion.fecha` como
`neo4j.time.Date`, no como `str` — al pasarlo a matplotlib rompía con
`float() argument ... not 'Date'`. Se arregló convirtiendo la fecha a
string directamente en el Cypher (`fecha: toString(r.fecha)`) en vez de
`.fecha`, para no depender de que cada consumidor Python haga la
conversión.
