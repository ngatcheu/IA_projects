"""Tests sans clé API ni serveur : Qdrant en mémoire et embedder factice."""

import hashlib
from pathlib import Path

from qdrant_client import QdrantClient

from iaprojects.chunking import load_markdown, split_by_headings
from iaprojects.ingest import ingest_dir
from iaprojects.store import VectorStore

RUNBOOK = """---
id: {id}
title: {title}
service: test
---
# {title}
## Symptômes
{body}
## Résolution
1. Étape un.
2. Étape deux.
"""


class FakeEmbedder:
    """Vecteurs déterministes dérivés du texte : suffisant pour tester la mécanique."""
    model_name = "fake/test-embedder"
    dim = 8

    def _vec(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255 + 0.01 for b in digest[: self.dim]]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


def write(dir_: Path, doc_id: str, body: str = "Un pod redémarre en boucle.") -> None:
    (dir_ / f"{doc_id}.md").write_text(RUNBOOK.format(id=doc_id, title=f"Runbook {doc_id}", body=body),
                                       encoding="utf-8")


def store() -> VectorStore:
    return VectorStore(QdrantClient(":memory:"), FakeEmbedder(), "runbooks")


def count(s: VectorStore) -> int:
    return s.client.count(s.collection).count


def test_chunking_keeps_sections_and_title(tmp_path):
    write(tmp_path, "RB-T1")
    doc = load_markdown(tmp_path / "RB-T1.md")
    chunks = split_by_headings(doc)
    assert doc.doc_id == "RB-T1"
    assert [c.section for c in chunks] == ["Runbook RB-T1", "Symptômes", "Résolution"]
    assert all(c.text.startswith("Runbook RB-T1 — ") for c in chunks)


def test_long_section_is_split_with_overlap(tmp_path):
    write(tmp_path, "RB-T2", body="x" * 4000)
    chunks = split_by_headings(load_markdown(tmp_path / "RB-T2.md"), max_chars=1500, overlap=200)
    assert sum(c.section == "Symptômes" for c in chunks) == 3


def test_ingestion_is_idempotent(tmp_path):
    write(tmp_path, "RB-T1")
    write(tmp_path, "RB-T2")
    s = store()
    first = ingest_dir(s, tmp_path)
    n = count(s)
    second = ingest_dir(s, tmp_path)
    assert (first.added, second.added, second.unchanged) == (2, 0, 2)
    assert count(s) == n                      # aucun doublon


def test_modified_document_replaces_old_chunks(tmp_path):
    write(tmp_path, "RB-T1", body="court")
    s = store()
    ingest_dir(s, tmp_path)
    write(tmp_path, "RB-T1", body="y" * 4000)  # plus de chunks
    report = ingest_dir(s, tmp_path)
    write(tmp_path, "RB-T1", body="court")     # moins de chunks : les anciens disparaissent
    ingest_dir(s, tmp_path)
    assert report.updated == 1
    assert count(s) == 3


def test_removed_document_is_deleted(tmp_path):
    write(tmp_path, "RB-T1")
    write(tmp_path, "RB-T2")
    s = store()
    ingest_dir(s, tmp_path)
    (tmp_path / "RB-T2.md").unlink()
    report = ingest_dir(s, tmp_path)
    assert report.deleted == 1
    assert {h.doc_id for h in s.search("pod", k=10)} == {"RB-T1"}
