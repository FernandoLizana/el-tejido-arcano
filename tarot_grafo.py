"""
Compatibilidad con el prototipo original.

Conserva el flujo visual de tarot_grafo.py usando el pipeline ArcanaGraph
(top-k + colores LAB) en lugar del umbral RGB denso.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards
from core.graph_builder import GraphBuilder
from core.utils import setup_logging
from visualization.plotly_graph import build_figure

logger = logging.getLogger("tarot_grafo_legacy")


def main() -> None:
    setup_logging()
    cards = load_all_cards()
    if not cards or not any(c.colores.dominantes_rgb for c in cards):
        logger.warning(
            "ADN sin colores. Ejecuta: python scripts/migrate_legacy_cartas.py"
        )
    builder = GraphBuilder()
    G = builder.build(cards, layer="color", strategy="top_k", top_k=4)
    fig = build_figure(
        G,
        dim=3,
        color_by="dominant",
        show_labels=False,
        title="Conexiones visuales entre cartas del Tarot (capa cromática · top-k)",
    )
    fig.show()


if __name__ == "__main__":
    main()
