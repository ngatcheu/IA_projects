#!/usr/bin/env bash
# Déploie l'environnement d'exécution des labs IA_projects (WSL ou Linux).
#
#   bash scripts/setup.sh              installation complète
#   bash scripts/setup.sh --sans-qdrant   sans démarrer Qdrant (module 1 seulement)
#
# Idempotent : chaque étape vérifie ce qui existe déjà avant d'agir. Aucun sudo.
# Étapes : uv -> Python 3.12 + dépendances -> .env -> modèle d'embedding -> Qdrant -> tests.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/env.sh
source scripts/env.sh

WITH_QDRANT=1
[[ "${1:-}" == "--sans-qdrant" ]] && WITH_QDRANT=0

ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die()  { printf '  \033[31m✘\033[0m %s\n' "$*" >&2; exit 1; }

step "1/6 Prérequis"
command -v python3 >/dev/null || die "python3 introuvable (sudo apt install python3 python3-pip)"
ok "python3 $(python3 --version | cut -d' ' -f2) (sert seulement à installer uv)"
if [[ $WITH_QDRANT == 1 ]]; then
  command -v docker >/dev/null || die "docker introuvable : installer Docker Desktop avec l'intégration WSL, ou relancer avec --sans-qdrant"
  docker info >/dev/null 2>&1 || die "Docker ne répond pas : démarrer Docker Desktop, ou relancer avec --sans-qdrant"
  ok "docker $(docker --version | cut -d' ' -f3 | tr -d ,)"
fi

step "2/6 uv (gestionnaire Python)"
if command -v uv >/dev/null; then
  ok "uv déjà présent : $(uv --version)"
else
  python3 -m pip install --user --quiet uv 2>/dev/null \
    || curl -LsSf https://astral.sh/uv/install.sh | sh
  command -v uv >/dev/null || die "installation de uv échouée"
  ok "uv installé : $(uv --version)"
fi

step "3/6 Python 3.12 et dépendances (pyproject.toml + uv.lock)"
uv sync --python 3.12 --quiet
ok "environnement : $UV_PROJECT_ENVIRONMENT ($("$UV_PROJECT_ENVIRONMENT/bin/python" --version))"

step "4/6 Fichier .env (clé API, jamais dans Git)"
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  warn ".env créé depuis .env.example : renseigner ANTHROPIC_API_KEY (nano .env)"
elif grep -qE '^ANTHROPIC_API_KEY=.+' .env; then
  chmod 600 .env
  ok ".env présent, ANTHROPIC_API_KEY renseignée"
else
  warn ".env présent mais ANTHROPIC_API_KEY vide : la recherche marche, pas la génération"
fi
git check-ignore -q .env && ok ".env bien ignoré par Git" || die ".env n'est PAS ignoré par Git : vérifier .gitignore"

step "5/6 Modèle d'embedding local (téléchargé une fois, ~220 Mo)"
uv run --quiet python - <<'PY'
from iaprojects.embeddings import default_embedder
e = default_embedder()
print(f"  \033[32m✔\033[0m {e.model_name} ({e.dim} dimensions)")
PY

step "6/6 Qdrant et tests"
if [[ $WITH_QDRANT == 1 ]]; then
  docker compose up -d --quiet-pull qdrant >/dev/null 2>&1 || die "docker compose up a échoué : docker compose up -d qdrant"
  for _ in $(seq 1 30); do
    curl -sf http://localhost:6333/readyz >/dev/null && break
    sleep 1
  done
  curl -sf http://localhost:6333/readyz >/dev/null || die "Qdrant ne répond pas sur http://localhost:6333"
  ok "Qdrant prêt : http://localhost:6333/dashboard"
else
  warn "Qdrant non démarré (--sans-qdrant)"
fi
uv run --quiet pytest -q -p no:warnings >/dev/null && ok "tests unitaires : OK" || die "tests unitaires en échec : uv run pytest"

printf '\n\033[1mEnvironnement prêt.\033[0m Dans chaque nouveau terminal : source scripts/env.sh\n'
