"""Configuration lue dans l'environnement (et .env en local). Aucun secret en dur."""

from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# Version de la stratégie de découpage : à incrémenter dès qu'elle change, car
# embedding + chunking + index forment un tout (module 9). Elle entre dans le nom
# de la collection.
CHUNKING_VERSION = "v1"


@dataclass(frozen=True)
class Settings:
    llm_model: str
    embedding_model: str
    qdrant_url: str
    corpus_dir: Path


@lru_cache
def settings() -> Settings:
    return Settings(
        llm_model=getenv("LLM_MODEL", "claude-opus-5-5"),
        embedding_model=getenv(
            "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        ),
        qdrant_url=getenv("QDRANT_URL", "http://localhost:6333"),
        corpus_dir=ROOT / "corpus",
    )
