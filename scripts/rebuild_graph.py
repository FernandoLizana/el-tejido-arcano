"""Reconstruye grafos por capa y registra processing run."""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.graph_builder import GraphBuilder  # noqa: E402
from core.metrics import graph_metrics  # noqa: E402
from core.utils import ensure_dir, load_pipeline_config, setup_logging, stable_hash  # noqa: E402
from visualization.plotly_graph import build_figure  # noqa: E402

logger = logging.getLogger("rebuild")


def main() -> None:
    setup_logging()
    pipe = load_pipeline_config()
    cards = load_all_cards()
    builder = GraphBuilder()
    out_dir = ensure_dir(ROOT / "data" / "cache" / "graphs")
    runs = ensure_dir(ROOT / "data" / "processing_runs")
    t0 = time.time()
    layers = ["color", "symbols", "semantic", "archetypes", "narrative", "combined"]
    summary = {}
    for layer in layers:
        G = builder.build(cards, layer=layer)  # type: ignore[arg-type]
        metrics = graph_metrics(G)
        summary[layer] = {
            "nodes": metrics["nodes"],
            "edges": metrics["edges"],
            "density": metrics["density"],
            "communities": len(metrics.get("communities") or []),
        }
        # serialize edges lightly
        payload = {
            "layer": layer,
            "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes()],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "weight": d.get("weight"),
                    "dimensions": d.get("dimensions"),
                    "explanation": d.get("explanation"),
                }
                for u, v, d in G.edges(data=True)
            ],
        }
        (out_dir / f"graph_{layer}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        fig = build_figure(G, dim=3, show_labels=False, title=f"Tejido Arcano — {layer}")
        fig.write_html(str(out_dir / f"graph_{layer}.html"))
        logger.info("Capa %s: %s aristas", layer, G.number_of_edges())

    run = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(time.time() - t0, 3),
        "seed": pipe.get("seed"),
        "pipeline": pipe,
        "cards_hash": stable_hash([c.model_dump(mode="json") for c in cards]),
        "summary": summary,
        "n_cards": len(cards),
        "model_version": pipe.get("model_version"),
    }
    run_path = runs / f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Processing run guardado: %s", run_path)


if __name__ == "__main__":
    main()
