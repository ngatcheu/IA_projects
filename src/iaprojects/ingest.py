"""Ingestion incrémentale et idempotente d'un dossier de Markdown (module 3).

    python -m iaprojects.ingest runbooks          # corpus/runbooks/*.md -> alias "runbooks"

- Un document inchangé (même hash) n'est pas recalculé.
- Un document modifié remplace tous ses anciens chunks.
- Un document retiré du dossier est supprimé de l'index.
Relancer la commande ne crée aucun doublon.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient

from iaprojects.chunking import load_markdown, split_by_headings
from iaprojects.config import settings
from iaprojects.embeddings import default_embedder
from iaprojects.store import VectorStore


@dataclass
class Report:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    chunks: int = 0


def ingest_dir(store: VectorStore, directory: Path) -> Report:
    store.ensure_collection()
    indexed = store.indexed_hashes()
    report = Report()
    seen: set[str] = set()

    for path in sorted(directory.glob("*.md")):
        doc = load_markdown(path)
        if doc.doc_id in seen:
            raise ValueError(f"identifiant en double : {doc.doc_id} ({path.name})")
        seen.add(doc.doc_id)
        if indexed.get(doc.doc_id) == doc.content_hash:
            report.unchanged += 1
            continue
        chunks = split_by_headings(doc)
        store.upsert_document(doc, chunks, source=path.name)
        report.chunks += len(chunks)
        if doc.doc_id in indexed:
            report.updated += 1
        else:
            report.added += 1

    for doc_id in indexed.keys() - seen:
        store.delete_document(doc_id)
        report.deleted += 1

    store.activate()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("corpus", help="sous-dossier de corpus/ (ex. : runbooks)")
    args = parser.parse_args()

    directory = settings().corpus_dir / args.corpus
    if not any(directory.glob("*.md")):
        raise SystemExit(f"aucun fichier .md dans {directory}")
    store = VectorStore(QdrantClient(url=settings().qdrant_url), default_embedder(), args.corpus)
    r = ingest_dir(store, directory)
    print(f"collection {store.collection} (alias {store.alias})")
    print(f"ajoutés {r.added} · modifiés {r.updated} · inchangés {r.unchanged} · supprimés {r.deleted} · chunks écrits {r.chunks}")


if __name__ == "__main__":
    main()
