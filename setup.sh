#!/usr/bin/env bash
# Instalación portable de El Tejido Arcano / ArcanaGraph Lab (Linux/macOS)
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "==> El Tejido Arcano — setup"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "No se encontró $PYTHON. Instala Python 3.11+." >&2
  exit 1
fi

"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
  echo "Se requiere Python 3.11 o superior." >&2
  exit 1
}

if [[ ! -x env/bin/python ]]; then
  echo "==> Creando entorno virtual en ./env"
  "$PYTHON" -m venv env
fi

echo "==> Instalando dependencias"
env/bin/python -m pip install --upgrade pip
env/bin/python -m pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> Creado .env desde .env.example"
fi

card_count=$(find data/cards -name 'major_*.json' 2>/dev/null | wc -l | tr -d ' ')
if [[ "${card_count:-0}" -lt 22 ]]; then
  echo "==> Sembrando ADN de 22 Arcanos Mayores"
  env/bin/python scripts/seed_major_arcana.py
  if [[ -d cartas ]]; then
    env/bin/python scripts/migrate_legacy_cartas.py
  fi
  env/bin/python scripts/validate_card_data.py
else
  echo "==> data/cards ya tiene $card_count cartas"
fi

if ! ls cartas/*.png >/dev/null 2>&1; then
  echo "Aviso: no hay PNGs en cartas/. Colócalos para el pipeline cromático." >&2
fi

cat <<'EOF'

Listo. Arranque:
  source env/bin/activate
  python -m streamlit run ui/app.py
  python -m uvicorn api.main:app --reload --port 8000
  python -m pytest tests -q
EOF
