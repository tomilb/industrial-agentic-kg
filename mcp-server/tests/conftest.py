import sys
from pathlib import Path

import pytest

_AQUI = Path(__file__).resolve()
sys.path.insert(0, str(_AQUI.parent.parent))  # mcp-server/ -> import server
sys.path.insert(0, str(_AQUI.parent.parent.parent / "graph"))  # graph/ -> import load_data


@pytest.fixture(scope="session")
def neo4j_driver():
    """Contenedor Neo4j efímero (testcontainers), compartido por TODOS los
    ficheros de test de integración de la sesión — evita arrancarlo una
    vez por fichero. Completamente aparte del Neo4j de desarrollo
    (docker-compose.yml): puerto aleatorio del host, sin volumen
    compartido, se destruye solo al terminar. Si Docker no está
    disponible, salta limpio con pytest.skip en vez de fallar."""
    from testcontainers.neo4j import Neo4jContainer

    try:
        container = Neo4jContainer("neo4j:5.24-community", password="test-password")
        container.start()
    except Exception as e:
        pytest.skip(f"Docker no disponible para tests de integración: {e}")

    driver = container.get_driver()
    try:
        yield driver
    finally:
        driver.close()
        container.stop()
