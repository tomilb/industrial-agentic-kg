# Roadmap — estado del proyecto

Este archivo es un checklist de trabajo, no memoria persistente — se actualiza
libremente y no se referencia desde CLAUDE.md como fuente de verdad estable.

## Fase 1 — Datos y grafo ✅ completa

- [x] Docker compose con Neo4j (community)
- [x] `graph/schema.cypher`: constraints y esquema de nodos/relaciones
- [x] `data-gen/generate.py`: histórico sintético de producción, 5 estaciones,
      ~6 meses de datos, con un cuello de botella deliberado en una estación
- [x] 5 máquinas con specs realistas + 5 candidatas de sustitución
- [x] `graph/load_data.py`: carga idempotente a Neo4j (MERGE, verificada con
      doble carga sin duplicar)
- [x] Validado manualmente contra Neo4j real

## Fase 2 — Servidor MCP y agente ✅ completa

- [x] Servidor MCP en Python (SDK oficial), transporte stdio
- [x] Tool `consultar_grafo`
- [x] Tool `calcular_financiero`
- [x] Tool `detectar_cuello_botella` (capacidad efectiva empírica, con
      fallback a OEE estático si no hay datos del periodo)
- [x] Conectado a Claude Desktop, verificado con preguntas reales de
      inversión y cuello de botella, incluyendo razonamiento correcto de
      teoría de restricciones (throughput de línea, no de máquina aislada)
- [x] Tests unitarios de las 3 tools con fixtures
- [x] Prompts/docstrings iterados hasta que las respuestas citan datos
      reales devueltos por las tools, no inventados

## Fase 3 — Informe y empaquetado portfolio ✅ completa

- [x] Plantilla corporativa de informe (logo + estructura de "empresa demo")
- [x] Tool `generar_informe` (docx, python-docx, 3 gráficas)
- [x] Generación de informe mensual/trimestral probada de extremo a extremo
- [x] README.md con arquitectura, capturas reales de demo
- [x] CLAUDE.md y ARCHITECTURE.md revisados y mantenidos al día
- [x] Repo publicado en GitHub

## Fase 4 — Calidad de ingeniería ✅ completa

A partir de una crítica objetiva del proyecto (perspectiva de entrevistador
Software/AI Engineer), se priorizaron 5 mejoras antes de añadir funcionalidad
nueva:

- [x] CI en GitHub Actions (tests automáticos en cada push/PR)
- [x] Test de regresión de contenido para `generar_informe` (duplicación,
      ids internos filtrados, formato de miles) — verificado reintroduciendo
      un bug real a mano y confirmando que el test lo detecta
- [x] `ruff` + `black` + `mypy` + pre-commit, con los hallazgos reales
      corregidos (incluida la investigación del caso límite de
      `mejora_capacidad_pct` y la decisión documentada de `python_version`
      distinto en mypy por compatibilidad de stubs de numpy)
- [x] Tests de integración reales contra Neo4j (`testcontainers`), aislados
      del Neo4j de desarrollo, verificados con `docker ps`
- [x] Limitaciones financieras reconocidas explícitamente en el README
- [x] Metodología de desarrollo con IA documentada, coautoría de Claude
      Code en commits aceptada y explicada

## Fase 5 — RAG híbrido: quinta tool `consultar_manual_tecnico` ✅ completa

- [x] `anos_en_servicio` añadido a `Maquina` (dato cuantitativo → grafo, no
      manuales) — bug real encontrado y corregido (el campo no llegaba a
      Neo4j pese a estar en el CSV)
- [x] 10 manuales técnicos redactados (M1-M5, C1-C5), con incidencias que
      se manifiestan deliberadamente en la estación siguiente de la línea
- [x] Embeddings locales (`sentence-transformers`, sin API key ni red en
      tiempo de ejecución) + índice vectorial nativo de Neo4j
- [x] `graph/load_manuals.py`, carga idempotente, chunking por sección
- [x] Tool `consultar_manual_tecnico`, con sobre-consulta al índice +
      filtrado por máquina (limitación real de Neo4j, verificada con test)
- [x] Preguntas de evaluación añadidas a `EVAL_QUESTIONS.md` antes de
      implementar (filas 9-14)
- [x] Verificado en Claude Desktop: separación correcta grafo/manual (fila
      14), contenido real recuperado (fila 9), y diagnóstico de causa raíz
      cruzando estaciones tras ajustar el docstring (fila 12)
- [x] `EXPLICACION_PROYECTO.md` y `GUION_VIDEO.md` actualizados con todo lo
      anterior

## Backlog — próximos pasos posibles

No comprometidos a un plazo concreto; mismo criterio que el resto del
proyecto: se abordarán si aportan señal real, no por completar la lista.

- [ ] **Evals automatizados** (determinista + LLM-as-judge vía API) —
      decisión explícita de dejarlo manual por ahora, ver entrada en
      `docs/DECISIONS.md` ("Verificación del agente: checklist manual, no
      evals automatizados") y la sección de limitaciones del README
- [ ] Soporte multi-línea (el esquema del grafo ya es genérico; falta
      quitar el atajo de "asumir la única línea" en 2-3 tools)
- [ ] Visualización estática/interactiva de la topología de línea con el
      cuello de botella resaltado
- [ ] Pipeline de ingesta MQTT → grafo en tiempo real (extensión natural
      de la experiencia previa en CTAG)
- [ ] Despliegue del servidor MCP de forma remota, para consumo desde una
      interfaz interna en vez de Claude Desktop
- [ ] Observabilidad ligera (logging estructurado de qué tool se llamó,
      con qué parámetros, latencia y tokens por conversación)