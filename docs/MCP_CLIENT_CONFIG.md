# Configuración del cliente MCP

## Claude Desktop

Añadir en el archivo de configuración de Claude Desktop (macOS:
`~/Library/Application Support/Claude/claude_desktop_config.json`;
Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "industrial-kg": {
      "command": "python",
      "args": ["/ruta/absoluta/al/repo/mcp-server/server.py"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "changeme"
      }
    }
  }
}
```

Reiniciar Claude Desktop tras guardar. Las 4 tools deberían aparecer
disponibles en el icono de herramientas de la conversación.

## Anthropic API (demo scriptada, opcional)

Para una demo reproducible desde el repo sin depender de la app de
escritorio, se puede invocar el mismo servidor vía el parámetro
`mcp_servers` de la API de Messages. Antes de implementarlo, confirmar en
la documentación oficial (docs.claude.com) la sintaxis vigente del conector
MCP, ya que es una función en evolución.
