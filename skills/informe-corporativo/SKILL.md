---
name: informe-corporativo
description: Genera el informe mensual/trimestral de producción de la línea en formato corporativo (docx), con KPIs, gráficas y detección de cuellos de botella del periodo. Usar siempre que el usuario pida un informe, resumen, reporte de producción, o mencione periodo mensual/trimestral en relación a la línea.
---

# Informe corporativo de producción

## Cuándo usar esta skill

Cuando el usuario pida un informe/resumen/reporte de producción de la línea,
para un periodo mensual o trimestral. No usar para preguntas puntuales de
tipo "¿cuál es el OEE de la estación X ahora mismo?" — eso se responde
directamente con la tool `consultar_grafo`, sin generar un documento.

## Qué debe contener el informe

1. Portada con nombre de la línea, periodo, fecha de generación
2. Resumen ejecutivo (3-4 líneas): unidades producidas, OEE medio, principal
   cuello de botella del periodo
3. Tabla de KPIs por estación (utilización, OEE, unidades, defectos)
4. Gráfica de producción diaria/semanal del periodo
5. Sección de cuello de botella: qué estación, por qué, evolución respecto
   al periodo anterior si hay datos
6. Recomendaciones (2-3 puntos, basadas en los datos, no genéricas)

## Cómo generar el documento

Todo esto lo hace la tool `generar_informe` del servidor MCP
(`mcp-server/server.py`) — el agente solo necesita llamarla con `periodo`
y, opcionalmente, `fecha_referencia`; no hay que ensamblar el documento a
mano desde la conversación.

1. `generar_informe` llama internamente a `detectar_cuello_botella` (dos
   veces: periodo actual y periodo anterior de igual duración, para la
   sección de evolución) y a `consultar_grafo`/`calcular_financiero` para
   las recomendaciones.
2. El documento se construye **desde cero** con `python-docx` — no hay
   plantilla `.docx` base. El logo ya está pre-generado en
   `assets/logo.png` (a partir de `assets/logo.svg`) y se embebe
   directamente; no se rasteriza en cada ejecución.
3. 3 gráficas con `matplotlib`, embebidas como imágenes en el docx:
   producción diaria total, OEE empírico por estación, y evolución de la
   capacidad efectiva de la restricción vs. el periodo anterior.
4. Encabezados con estilos nativos de Word (Heading 1/2 vía
   `doc.add_heading`), no negrita simulando un título.
5. Las recomendaciones citan cifras concretas devueltas por las tools —
   nunca texto fijo con huecos rellenados (detalle del cálculo en
   `docs/DECISIONS.md`).
6. Se guarda en
   `reports/output/informe_<periodo>_<fecha_referencia>.docx`.

## Recursos

- `assets/logo.svg` — logo vectorial de la marca demo (NEXATRON
  Electronics).
- `assets/logo.png` (480×120) — versión rasterizada del logo, generada una
  vez y versionada; es la que se embebe en el docx. Si el logo de marca
  cambia, hay que regenerar este PNG a mano (no hay pipeline de
  rasterización automática: `cairosvg` no funciona en Windows sin GTK3
  runtime instalado a nivel de sistema, así que se descartó).
