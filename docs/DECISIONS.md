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
