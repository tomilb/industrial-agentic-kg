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

1. Llamar a `detectar_cuello_botella` y a `consultar_grafo` (registros de
   producción del periodo) para obtener todos los datos necesarios antes de
   escribir nada.
2. Usar `assets/plantilla.docx` como base (logo y estilos de la "empresa
   demo") — no crear el documento desde cero.
3. Generar las gráficas con matplotlib y embeberlas como imágenes en el
   docx (ver `python-docx` en requirements.txt).
4. Guardar el resultado en `reports/output/informe_<periodo>.docx`.

## Recursos

- `assets/plantilla.docx` — plantilla corporativa (logo/colores de la
  empresa demo). **Pendiente de crear** — sustituir por una plantilla real
  antes de la Semana 3.
