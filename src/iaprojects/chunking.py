"""Parsing des runbooks Markdown et découpage par structure (module 3).

Format d'un runbook : un en-tête YAML (métadonnées) puis du Markdown.

    ---
    id: RB-012
    title: ...
    service: svc-paiements
    classification: interne
    allowed_groups: [infra, astreinte]
    ---
    # Titre
    ## Symptômes
    ...
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING = re.compile(r"(?m)^(?=#{1,3} )")


@dataclass
class Document:
    doc_id: str
    title: str
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """Empreinte du contenu : seule une modification entraîne une réindexation."""
        payload = yaml.safe_dump(self.metadata, sort_keys=True) + self.text
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Chunk:
    doc_id: str
    index: int
    section: str
    text: str


def load_markdown(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FRONT_MATTER.match(raw)
    meta = yaml.safe_load(match.group(1)) if match else {}
    body = raw[match.end():] if match else raw
    doc_id = str(meta.get("id") or path.stem)
    return Document(doc_id=doc_id, title=str(meta.get("title", doc_id)), text=body.strip(), metadata=meta)


def split_by_headings(doc: Document, max_chars: int = 1500, overlap: int = 200) -> list[Chunk]:
    """Une section (titre de niveau 1 à 3) = un chunk ; les sections trop longues sont
    recoupées avec chevauchement. Chaque chunk est préfixé du titre du document et de sa
    section, pour qu'il reste compréhensible hors contexte."""
    chunks: list[Chunk] = []
    for section in filter(None, (s.strip() for s in HEADING.split(doc.text))):
        title = section.splitlines()[0].lstrip("# ").strip()
        start = 0
        while start < len(section):
            piece = section[start:start + max_chars]
            chunks.append(Chunk(doc.doc_id, len(chunks), title, f"{doc.title} — {title}\n\n{piece}"))
            if start + max_chars >= len(section):
                break
            start += max_chars - overlap
    return chunks
