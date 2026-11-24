"""Embeddings locaux (fastembed, ONNX, CPU) : aucune donnée envoyée à l'extérieur.

Le même modèle sert à indexer et à interroger ; en changer impose de réindexer
(son nom entre dans le nom de la collection, voir store.py).
"""

import re
from functools import lru_cache
from typing import Protocol

from fastembed import TextEmbedding

from iaprojects.config import settings


class Embedder(Protocol):
    model_name: str
    dim: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = TextEmbedding(model_name)
        self.dim = len(next(iter(self._model.embed(["dimension"]))))
        # Les modèles e5 attendent des préfixes distincts pour requête et passage.
        self._e5 = "e5" in model_name.lower()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._e5:
            texts = [f"passage: {t}" for t in texts]
        return [v.tolist() for v in self._model.embed(texts, batch_size=32)]

    def embed_query(self, text: str) -> list[float]:
        if self._e5:
            text = f"query: {text}"
        return next(iter(self._model.embed([text]))).tolist()


def model_slug(model_name: str) -> str:
    """Nom court et sûr pour un nom de collection : 'paraphrase-multilingual-MiniLM-L12-v2' -> 'paraphrase-multilingual-minilm-l12-v2'."""
    return re.sub(r"[^a-z0-9]+", "-", model_name.split("/")[-1].lower()).strip("-")


@lru_cache
def default_embedder() -> FastEmbedder:
    return FastEmbedder(settings().embedding_model)
