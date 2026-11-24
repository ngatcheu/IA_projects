# Module 1 — image du prototype RAG minimal.
# Contexte de construction : ce dossier (Formations/module-01-fondamentaux).
FROM python:3.12-slim

ARG VERSION=1.0.0
LABEL org.opencontainers.image.title="ia-projects/module-01" \
      org.opencontainers.image.description="Module 1 — prototype RAG minimal (Banque Horizon)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.source="https://github.com/ngatcheu/IA_projects"

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/opt/fastembed

WORKDIR /module

# Dépendances verrouillées (uv.lock du module)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Modèle d'embedding embarqué : aucun téléchargement à l'exécution
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('${EMBEDDING_MODEL}')"

# Code et mini-corpus du module
COPY code ./code

ARG UID=1000
RUN useradd --uid ${UID} --create-home app && chown -R app /opt/fastembed
USER app

ENTRYPOINT ["python", "code/prototype.py"]
CMD ["--help"]
