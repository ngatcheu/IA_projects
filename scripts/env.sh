# À sourcer dans chaque nouveau terminal : `source scripts/env.sh`
# Rend `uv` accessible et place l'environnement Python hors du disque Windows
# (/mnt/c est lent sous WSL).
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/ia-projects"
export UV_LINK_MODE=copy
# Cache durable des modèles d'embedding (par défaut fastembed utilise /tmp, vidé au redémarrage)
export FASTEMBED_CACHE_PATH="$HOME/.cache/fastembed"
