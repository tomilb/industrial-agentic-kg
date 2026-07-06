"""Lee manuales/*.md, trocea por sección (cada `##` es un chunk), calcula
embeddings con sentence-transformers, y carga a Neo4j.

Idempotente: igual que load_data.py, toda escritura usa MERGE anclado en
un id determinista (`{maquina_id}-{slug(seccion)}`).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml
from neo4j import Driver
from sentence_transformers import SentenceTransformer

# 384 dim, multilingüe (incl. español), local — sin API key ni red tras
# la primera descarga. Debe coincidir con el `vector.dimensions` de
# graph/schema.cypher y con MODELO_EMBEDDINGS en mcp-server/server.py.
MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"

MANUALES_DIR = Path(__file__).parent.parent / "manuales"


def _slug(texto: str) -> str:
    """ "Precauciones de seguridad" -> "precauciones-de-seguridad" (sin acentos)."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower()).strip("-")


def _parsear_manual(ruta: Path) -> tuple[dict, list[tuple[str, str]]]:
    """Devuelve (frontmatter, [(titulo_seccion, texto), ...])."""
    texto = ruta.read_text(encoding="utf-8")
    _, frontmatter_raw, cuerpo = texto.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_raw)

    secciones = []
    for bloque in re.split(r"^## ", cuerpo, flags=re.MULTILINE)[1:]:
        titulo, _, resto = bloque.partition("\n")
        secciones.append((titulo.strip(), resto.strip()))
    return frontmatter, secciones


def construir_chunks(manuales_dir: Path = MANUALES_DIR) -> list[dict]:
    """Un chunk por sección `##` de cada manuales/*.md — no el documento
    completo de golpe, para que cada chunk responda a un único tema
    (mantenimiento, seguridad, etc.) sin mezclar contenido irrelevante."""
    chunks = []
    for ruta in sorted(manuales_dir.glob("*.md")):
        frontmatter, secciones = _parsear_manual(ruta)
        maquina_id = frontmatter["maquina_id"]
        for seccion, texto in secciones:
            chunks.append(
                {
                    "id": f"{maquina_id}-{_slug(seccion)}",
                    "maquina_id": maquina_id,
                    "seccion": seccion,
                    "texto": texto,
                }
            )
    return chunks


def calcular_embeddings(chunks: list[dict], modelo: SentenceTransformer) -> list[dict]:
    embeddings = modelo.encode([c["texto"] for c in chunks], normalize_embeddings=True)
    return [
        {**chunk, "embedding": embedding.tolist()}
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]


def cargar_manual_chunks(driver: Driver, rows: list[dict]) -> None:
    def _tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (m {id: row.maquina_id})
            WHERE m:Maquina OR m:MaquinaCandidata
            MERGE (chunk:ManualChunk {id: row.id})
            SET chunk.maquina_id = row.maquina_id,
                chunk.seccion = row.seccion,
                chunk.texto = row.texto,
                chunk.embedding = row.embedding
            MERGE (m)-[:TIENE_MANUAL]->(chunk)
            """,
            rows=rows,
        )

    with driver.session() as session:
        session.execute_write(_tx, rows)


def main() -> None:
    from load_data import aplicar_schema, get_driver  # mismo directorio graph/

    driver = get_driver()
    try:
        aplicar_schema(driver)  # idempotente: por si se ejecuta antes que load_data.py
        chunks = construir_chunks()
        modelo = SentenceTransformer(MODELO_EMBEDDINGS)
        chunks_con_embedding = calcular_embeddings(chunks, modelo)
        cargar_manual_chunks(driver, chunks_con_embedding)
        print(f"Cargados {len(chunks_con_embedding)} chunks de manual técnico.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
