"""Client Claude unique pour tous les labs.

Un seul point d'entrée : changer de modèle ou de fournisseur ne touche que ce module
(réversibilité, module 17).

- Repli serveur en cas de refus du filtre de sécurité (`fallbacks="default"`) : la
  requête est rejouée sur un modèle de repli dans le même appel.
- Le SDK réessaie déjà les erreurs transitoires (429, 5xx, réseau) avec backoff.
"""

from functools import lru_cache

import anthropic
from pydantic import BaseModel

from iaprojects.config import settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class RefusedError(RuntimeError):
    """Le modèle (et son repli) a décliné la requête."""


@lru_cache
def client() -> anthropic.Anthropic:
    # Identifiants résolus par le SDK : ANTHROPIC_API_KEY (.env), ou profil `ant auth login`.
    return anthropic.Anthropic(max_retries=4)


def _check(response) -> None:
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise RefusedError(f"requête déclinée (catégorie : {category})")


def generate_text(
    system: str, prompt: str, *, effort: str = "medium", max_tokens: int = 8000
) -> str:
    """Génération de texte libre (ex. : corpus synthétique)."""
    response = client().beta.messages.create(
        model=settings().llm_model,
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": effort},
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    _check(response)
    return "".join(b.text for b in response.content if b.type == "text").strip()


def generate_structured[T: BaseModel](
    system: str, prompt: str, schema: type[T], *, effort: str = "low", max_tokens: int = 4000
) -> T:
    """Sortie structurée validée par Pydantic : le schéma est le contrat (module 12)."""
    response = client().beta.messages.parse(
        model=settings().llm_model,
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": effort},
        # Consignes stables en tête et mises en cache ; la partie variable vient après.
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    _check(response)
    return response.parsed_output
