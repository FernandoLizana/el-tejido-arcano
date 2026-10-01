"""Analizador de tiradas y caminos ocultos."""

from __future__ import annotations

import logging
from typing import Any, Literal

import networkx as nx

from core.card_repository import index_cards, load_all_cards
from core.graph_builder import GraphBuilder
from core.metrics import (
    archetypal_distance,
    bridge_card,
    internal_tension,
    missing_patterns,
    narrative_coherence,
    resonance_index,
    safe_distance,
    spread_density,
    symbolic_entropy,
)
from core.similarity_engine import SimilarityEngine
from schemas.card_schema import CardDNA, SpreadAnalyzeResult

logger = logging.getLogger(__name__)

PathMode = Literal["max_similarity", "narrative", "archetypal", "contrast", "chromatic"]


class SpreadAnalyzer:
    def __init__(self, builder: GraphBuilder | None = None) -> None:
        self.builder = builder or GraphBuilder()
        self.engine = self.builder.engine

    def analyze(
        self,
        card_ids: list[str],
        cards: list[CardDNA] | None = None,
        profile: str | None = None,
    ) -> SpreadAnalyzeResult:
        catalog = index_cards(cards or load_all_cards())
        selected = [catalog[i] for i in card_ids if i in catalog]
        if len(selected) != len(card_ids):
            missing = set(card_ids) - set(catalog)
            raise KeyError(f"Cartas no encontradas: {missing}")

        # grafo global para caminos; subgrafo por pares de la tirada
        G_full = self.builder.build(list(catalog.values()), layer="combined", profile=profile)
        # Forzar subgrafo completo entre cartas de la tirada con similitudes
        G_sub = nx.Graph()
        for c in selected:
            G_sub.add_node(c.id, **G_full.nodes[c.id])
        pair_results = []
        for i, a in enumerate(selected):
            for b in selected[i + 1 :]:
                res = self.engine.compare(a, b, profile=profile)
                pair_results.append(res)
                G_sub.add_edge(
                    a.id,
                    b.id,
                    weight=res.similarity_total,
                    dimensions=res.dimensions.model_dump(),
                    explanation=res.explanation.model_dump(),
                )

        dens = spread_density(G_sub)
        ent = symbolic_entropy(selected)
        bridge = bridge_card(G_sub)

        strongest = dens["strongest_pairs"][0] if dens["strongest_pairs"] else None
        # tensión: mayor tension_score entre pares
        tension_best = None
        best_t = -1.0
        for res in pair_results:
            t = internal_tension(res.dimensions.model_dump())
            if t["tension_score"] > best_t:
                best_t = t["tension_score"]
                tension_best = {
                    "a": res.card_a,
                    "b": res.card_b,
                    **t,
                    "similarity_total": res.similarity_total,
                }

        # patrones dominantes
        from collections import Counter

        symbols = Counter(s for c in selected for s in c.simbolos)
        emotions = Counter(e for c in selected for e in c.emociones)
        elements = Counter(e for c in selected for e in c.elementos)
        colors = []
        for c in selected:
            if c.colores.dominantes_hex:
                colors.append(c.colores.dominantes_hex[0])

        hidden = []
        if len(selected) >= 2:
            path = find_hidden_path(
                selected[0].id,
                selected[-1].id,
                G_full,
                self.engine,
                catalog,
                profile=profile,
                max_depth=4,
            )
            if path:
                hidden.append(path)

        # carta central: mayor weighted degree local o media
        central = None
        if G_sub.number_of_nodes():
            wd = dict(G_sub.degree(weight="weight"))
            central_id = max(wd, key=wd.get)
            central = {"card_id": central_id, "weighted_degree": wd[central_id]}

        return SpreadAnalyzeResult(
            cards=card_ids,
            metrics={
                "density": dens,
                "entropy": ent,
                "resonance_mean": float(
                    sum(resonance_index(r.similarity_total) for r in pair_results) / max(len(pair_results), 1)
                ),
                "central_card": central,
            },
            dominant_patterns={
                "symbols": symbols.most_common(8),
                "emotions": emotions.most_common(8),
                "elements": elements.most_common(8),
                "colors": colors,
            },
            missing_patterns=missing_patterns(selected),
            bridge_card=bridge,
            strongest_pair=strongest,
            tension_pair=tension_best,
            hidden_paths=hidden,
            narrative_hypotheses=narrative_coherence(selected),
        )


def find_hidden_path(
    card_a: str,
    card_b: str,
    G: nx.Graph,
    engine: SimilarityEngine | None = None,
    catalog: dict[str, CardDNA] | None = None,
    profile: str | None = None,
    max_depth: int = 4,
    mode: PathMode = "max_similarity",
) -> dict[str, Any] | None:
    """Camino entre dos cartas evitando ciclos; profundidad limitada."""
    if card_a not in G or card_b not in G:
        return None

    H = G.copy()
    for u, v, d in H.edges(data=True):
        w = d.get("weight", 0.0)
        dims = d.get("dimensions") or {}
        if mode == "chromatic":
            w = float(dims.get("color", w))
        elif mode == "archetypal":
            w = float(dims.get("archetypes", w))
        elif mode == "narrative":
            w = float(dims.get("narrative", w))
        elif mode == "contrast":
            # favorecer aristas con tensión (similitud media pero dims dispares)
            vals = list(dims.values()) if dims else [w]
            w = float(max(vals) - min(vals)) if vals else w
        d["mode_weight"] = w
        d["dist"] = safe_distance(w) + 1e-6

    try:
        # restringir profundidad via caminos simples cortos
        paths = list(nx.all_simple_paths(H, card_a, card_b, cutoff=max_depth))
    except (nx.NetworkXError, nx.NodeNotFound):
        return None
    if not paths:
        # fallback shortest
        info = archetypal_distance(H, card_a, card_b)
        if not info["path"]:
            return None
        paths = [info["path"]]

    def path_score(path: list[str]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            total += H[path[i]][path[i + 1]].get("mode_weight", 0)
        return total / max(len(path) - 1, 1)

    best = max(paths, key=path_score)
    alts = sorted(paths, key=path_score, reverse=True)[1:4]

    steps = []
    for i in range(len(best) - 1):
        u, v = best[i], best[i + 1]
        data = H[u][v]
        steps.append(
            {
                "from": u,
                "to": v,
                "weight": data.get("mode_weight", data.get("weight")),
                "dimensions": data.get("dimensions"),
                "explanation": data.get("explanation"),
            }
        )

    return {
        "sequence": best,
        "score": path_score(best),
        "steps": steps,
        "alternatives": alts,
        "mode": mode,
        "max_depth": max_depth,
        "profile": profile,
        "warning": (
            "Construcción del modelo: el camino depende del grafo, pesos y modo; "
            "no constituye una secuencia necesariamente tradicional del Tarot."
        ),
    }
