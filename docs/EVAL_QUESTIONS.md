# Preguntas de evaluación del agente

Checklist manual para la Semana 2. Para cada pregunta: anotar qué tool(s)
llamó el agente, si los datos citados coinciden con lo cargado en Neo4j, y
si la respuesta es correcta. Un "no" en cualquiera de las tres columnas es
un fallo a corregir antes de dar por cerrada la tool correspondiente.

| # | Pregunta | Tool(s) esperada(s) | Verificado manualmente |
|---|---|---|---|
| 1 | ¿Si incorporo la máquina candidata [C1] en la estación [E2], en cuánto mejora el throughput y cuándo recupero la inversión? | `consultar_grafo` + `calcular_financiero` | [ ] |
| 2 | Entre [C1] y [C2] como sustitutas de [M3], ¿cuál tiene mejor ROI a 3 años? | `consultar_grafo` + `calcular_financiero` (x2) | [ ] |
| 3 | ¿Qué estación es el cuello de botella de la línea en el último trimestre? | `detectar_cuello_botella` | [ ] |
| 4 | ¿Cómo ha evolucionado el OEE de la estación [E1] en los últimos 6 meses? | `consultar_grafo` | [ ] |
| 5 | Dado el histórico de producción, ¿en qué campo flojea más la línea y qué recomiendas? | `detectar_cuello_botella` + `consultar_grafo` | [ ] |
| 6 | Genera el informe del último trimestre de la línea. | `generar_informe` | [ ] |
| 7 | Pregunta fuera de alcance (p.ej. "¿qué tiempo hará mañana?") — el agente debe declinar con claridad, no inventar una respuesta usando las tools. | ninguna | [ ] |
| 8 | Pregunta con datos inexistentes (p.ej. máquina que no está en el grafo) — el agente debe decir que no tiene esos datos, no inventar cifras. | `consultar_grafo` (resultado vacío) | [ ] |
| 9 | ¿Qué mantenimiento preventivo necesita el AOI? | `consultar_manual_tecnico` | [ ] |
| 10 | ¿Qué precauciones de seguridad tiene el cobot de ensamblaje? | `consultar_manual_tecnico` | [ ] |
| 11 | Si sustituyo el AOI por la candidata con IA, ¿qué necesito preparar antes de la instalación? | `consultar_manual_tecnico` (+ `consultar_grafo` opcional) | [ ] |
| 12 | Está subiendo el rechazo en el AOI, ¿por qué podría ser? | `consultar_manual_tecnico` + `consultar_grafo`/`detectar_cuello_botella` | [ ] |
| 13 | ¿Cuánto tardaría en tener la nueva AOI operando a plena capacidad, y afecta eso al payback calculado? | `consultar_manual_tecnico` + `calcular_financiero` | [ ] |
| 14 | ¿Cuánto cuesta la máquina de inspección óptica? | `consultar_grafo` — **nunca** `consultar_manual_tecnico` | [ ] |

Casos 7 y 8 son tan importantes como los positivos — un agente que inventa
cifras financieras es peor que uno que se calla.

El caso 14 es el más importante de los seis nuevos: verifica que ninguna
cifra (coste, capacidad, ROI) se responde citando el contenido de un
manual técnico, aunque el manual mencione esa máquina — los números
siempre deben venir de `consultar_grafo` o `calcular_financiero`. Si el
agente alguna vez da un precio "recordado" del texto de un manual en vez
de consultado al grafo, es un fallo de diseño, no una respuesta válida
por otro camino.