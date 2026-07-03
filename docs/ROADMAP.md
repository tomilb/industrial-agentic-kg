# Roadmap — MVP en 3 semanas

Este archivo es un checklist de trabajo, no memoria persistente — se actualiza
libremente y no se referencia desde CLAUDE.md como fuente de verdad estable.

## Semana 1 — Datos y grafo

- [ ] Docker compose con Neo4j (community)
- [ ] `graph/schema.cypher`: constraints y esquema de nodos/relaciones
- [ ] `data-gen/generate.py`: histórico sintético de producción, 5 estaciones,
      ~6 meses de datos, con un cuello de botella deliberado en una estación
- [ ] 4-5 máquinas con specs realistas + 2-3 candidatas de sustitución cada una
- [ ] `graph/load_data.py`: carga a Neo4j
- [ ] Validar manualmente con 5-6 queries Cypher representativas

## Semana 2 — Servidor MCP y agente

- [ ] Servidor MCP en Python (SDK oficial), transporte stdio
- [ ] Tool `consultar_grafo`
- [ ] Tool `calcular_financiero`
- [ ] Tool `detectar_cuello_botella`
- [ ] Conectar a Claude Desktop, probar las preguntas del enunciado original
      ("¿si incorporo la máquina X...?", "¿cómo gestiono este cuello de
      botella?")
- [ ] Tests unitarios de las 3 tools con fixtures
- [ ] Iterar prompts/descripciones de tools hasta que las respuestas citen
      datos reales devueltos por las tools, no inventados

## Semana 3 — Informe y empaquetado portfolio

- [ ] Plantilla corporativa de informe (Skill) con estructura + imágenes
      de una "empresa demo"
- [ ] Tool `generar_informe`
- [ ] Probar generación de informe mensual/trimestral de extremo a extremo
- [ ] README.md con arquitectura, capturas, GIF de una conversación real
- [ ] Revisar CLAUDE.md y ARCHITECTURE.md por si algo quedó desactualizado
- [ ] Publicar repo en GitHub + post en LinkedIn
