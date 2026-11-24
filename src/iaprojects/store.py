"""Index vectoriel Qdrant.

- Collection nommée avec ses versions : `<corpus>_emb-<modèle>_chunk-<version>`.
  Changer de modèle ou de découpage crée une nouvelle collection à côté de l'ancienne.
- Un alias stable (`<corpus>`) pointe sur la collection active : bascule et retour
  arrière se font en déplaçant l'alias (bleu-vert, module 9).
- Identifiants de points déterministes (doc_id + rang) : réindexer écrase, ne duplique pas.
"""

import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from iaprojects.chunking import Chunk, Document
from iaprojects.config import CHUNKING_VERSION
from iaprojects.embeddings import Embedder, model_slug

NAMESPACE = uuid.UUID("6f1c2a10-4b7e-4f3a-9d2b-1a2b3c4d5e6f")


@dataclass
class Hit:
    doc_id: str
    title: str
    section: str
    text: str
    score: float
    source: str


class VectorStore:
    def __init__(self, client: QdrantClient, embedder: Embedder, corpus: str):
        self.client = client
        self.embedder = embedder
        self.alias = corpus
        self.collection = f"{corpus}_emb-{model_slug(embedder.model_name)}_chunk-{CHUNKING_VERSION}"

    # -- cycle de vie --------------------------------------------------------
    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(size=self.embedder.dim, distance=models.Distance.COSINE),
            )
            self.client.create_payload_index(self.collection, "doc_id", models.PayloadSchemaType.KEYWORD)

    def activate(self) -> None:
        """Fait pointer l'alias sur cette collection (atomique)."""
        ops: list = []
        existing = {a.alias_name for a in self.client.get_aliases().aliases}
        if self.alias in existing:
            ops.append(models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=self.alias)))
        ops.append(models.CreateAliasOperation(
            create_alias=models.CreateAlias(collection_name=self.collection, alias_name=self.alias)))
        self.client.update_collection_aliases(change_aliases_operations=ops)

    # -- écriture --------------------------------------------------------------
    def indexed_hashes(self) -> dict[str, str]:
        """doc_id -> hash du contenu indexé (lu sur le premier chunk de chaque document)."""
        hashes: dict[str, str] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                self.collection, limit=256, offset=offset,
                with_payload=["doc_id", "content_hash"], with_vectors=False)
            for p in points:
                hashes.setdefault(p.payload["doc_id"], p.payload["content_hash"])
            if offset is None:
                return hashes

    def delete_document(self, doc_id: str) -> None:
        self.client.delete(self.collection, points_selector=models.FilterSelector(filter=models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))])))

    def upsert_document(self, doc: Document, chunks: list[Chunk], source: str) -> None:
        # Supprimer d'abord : une nouvelle version peut avoir moins de chunks.
        self.delete_document(doc.doc_id)
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        points = [
            models.PointStruct(
                id=str(uuid.uuid5(NAMESPACE, f"{doc.doc_id}#{c.index}")),
                vector=vec,
                payload={
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "section": c.section,
                    "text": c.text,
                    "source": source,
                    "content_hash": doc.content_hash,
                    "classification": doc.metadata.get("classification", "interne"),
                    "allowed_groups": doc.metadata.get("allowed_groups", []),
                    "embedding_model": self.embedder.model_name,
                    "chunking_version": CHUNKING_VERSION,
                },
            )
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(self.collection, points=points, wait=True)

    # -- lecture ----------------------------------------------------------------
    def search(self, query: str, k: int = 5) -> list[Hit]:
        result = self.client.query_points(
            self.alias, query=self.embedder.embed_query(query), limit=k, with_payload=True)
        return [
            Hit(p.payload["doc_id"], p.payload["title"], p.payload["section"],
                p.payload["text"], p.score, p.payload["source"])
            for p in result.points
        ]
