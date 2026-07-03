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

Casos 7 y 8 son tan importantes como los positivos — un agente que inventa
cifras financieras es peor que uno que se calla.
