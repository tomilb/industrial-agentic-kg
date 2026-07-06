# CLAUDE.md

## Qué es este proyecto

Industrial Agentic Knowledge Graph: un agente conversacional que razona sobre el
estado de una línea de producción industrial (máquinas, costes, histórico de
producción) modelada como un grafo en Neo4j. El agente responde preguntas de
inversión ("¿si sustituyo esta máquina por esta otra, cuándo recupero la
inversión?"), optimización y detección de cuellos de botella, y genera informes
periódicos con formato corporativo usando Skills.

Portfolio técnico — prioridad: código correcto y bien razonado por encima de
features extra. Alcance de MVP: 2-3 semanas.

## Stack

- Python 3.11+
- Neo4j 5.x (Docker, community edition)
- MCP Python SDK (servidor local, transporte stdio)
- Cliente: Claude Desktop y/o Anthropic API (`mcp_servers`)
- pandas / numpy para datos sintéticos
- Pydantic para validar schemas de entrada/salida de las tools

## Estructura del repo

```
/data-gen/       generador de datos sintéticos de producción
/graph/          schema.cypher + load_data.py (carga a Neo4j)
/mcp-server/     servidor MCP con las 4 tools (ver ARCHITECTURE.md)
/reports/        plantilla corporativa + informes generados (Skills)
/docs/           DECISIONS.md, ROADMAP.md
/ARCHITECTURE.md esquema del grafo y contratos de las tools
```

## Comandos

- Levantar Neo4j: `docker compose up -d neo4j`
- Cargar esquema y datos: `python graph/load_data.py`
- Cargar manuales técnicos (RAG): `python graph/load_manuals.py` (1ª vez
  descarga el modelo de embeddings, ~460 MB)
- Generar datos sintéticos: `python data-gen/generate.py --stations 5 --days 180`
- Arrancar servidor MCP: `python mcp-server/server.py`
- Tests: `pytest mcp-server/tests --ignore-glob="mcp-server/tests/test_integration_*.py"`
- Tests de integración (requieren Docker corriendo): `pytest mcp-server/tests -m integration`

## Convenciones

- Type hints obligatorios en todo el código Python.
- Toda tool MCP devuelve JSON validado con un modelo Pydantic (contratos en
  ARCHITECTURE.md) — no devolver dicts sueltos.
- Nombres de nodos/relaciones del grafo en el estilo ya fijado en
  ARCHITECTURE.md (`Maquina`, `PUEDE_SUSTITUIRSE_POR`) — no introducir
  variantes.
- Mínimo un test por tool MCP, contra fixtures locales, no contra el Neo4j
  real.
- Commits pequeños y descriptivos; un commit por tool o por script, no un
  commit único al final del día.

## Reglas siempre / nunca

- NUNCA hardcodear credenciales de Neo4j — usar variables de entorno
  (`.env`, no versionado; `.env.example` sí versionado).
- SIEMPRE que una tool falle, devolver un error estructurado
  (`{"error": "..."}`) — no dejar propagar una excepción sin capturar hacia
  el cliente MCP.
- SIEMPRE que se añada una tool nueva, documentar su schema en
  ARCHITECTURE.md antes de implementarla, no después.
- SIEMPRE que se tome una decisión de diseño no trivial (librería, patrón,
  corte de alcance), registrarla en `docs/DECISIONS.md` con una línea de
  motivo.

## Dónde mirar más

- Arquitectura, esquema del grafo y contratos de las tools: `ARCHITECTURE.md`
- Decisiones de diseño y alternativas descartadas: `docs/DECISIONS.md`
- Plan de las 3 semanas: `docs/ROADMAP.md`
