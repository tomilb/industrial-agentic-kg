import sys
from pathlib import Path

_AQUI = Path(__file__).resolve()
sys.path.insert(0, str(_AQUI.parent.parent))  # mcp-server/ -> import server
sys.path.insert(0, str(_AQUI.parent.parent.parent / "graph"))  # graph/ -> import load_data
