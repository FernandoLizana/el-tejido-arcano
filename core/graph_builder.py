"""Construcción de grafos multicapa con estrategias top-k / umbral."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

import networkx as nx

from core.card_repository import load_all_cards
from core.similarity_engine import SimilarityEngine
from core.utils import load_pipeline_config
from schemas.card_schema import CardDNA, SimilarityResult

logger = logging.getLogger(__name__)

LayerName = Literal[
    "color",
    "symbols",
    "semantic",
    "archetypes",
    "emotions",
    "narrative",
    "combined",
]


class GraphBuilder:
    def __init__(self, engine: SimilarityEngine | None = None, profile: str | None = None) -> None:
        self.engine = engine or SimilarityEngine(profile=profile)
        pipe = load_pipeline_config()
        gcfg = pipe.get("graph", {})
        self.strategy = gcfg.get("strategy", "top_k")
        self.top_k = int(gcfg.get("top_k", 4))
        self.threshold = float(gcfg.get("threshold", 0.55))
        self.mutual_top_k = bool(gcfg.get("mutual_top_k", False))
        self.model_version = pipe.get("model_version", "1.0.0-iter1")

    def pairwise(
        self, cards: list[CardDNA], profile: str | None = None
    ) -> dict[tuple[str, str], SimilarityResult]:
        self.engine.fit_corpus(cards)
        results: dict[tuple[str, str], SimilarityResult] = {}
        for i, a in enumerate(cards):
            for b in cards[i + 1 :]:
                res = self.engine.compare(a, b, profile=profile)
                key = tuple(sorted((a.id, b.id)))
                results[key] = res
        return results

    def _score_for_layer(self, res: SimilarityResult, layer: LayerName) -> float:
        if layer == "combined":
            return res.similarity_total
        return float(getattr(res.dimensions, layer if layer != "symbols" else "symbols"))

    def build(
        self,
        cards: list[CardDNA] | None = None,
        layer: LayerName = "combined",
        profile: str | None = None,
        strategy: str | None = None,
        top_k: int | None = None,
        threshold: float | None = None,
        mutual_top_k: bool | None = None,
    ) -> nx.Graph:
        cards = cards or load_all_cards()
        strategy = strategy or self.strategy
        top_k = self.top_k if top_k is None else top_k
        threshold = self.threshold if threshold is None else threshold
        mutual_top_k = self.mutual_top_k if mutual_top_k is None else mutual_top_k

        pairs = self.pairwise(cards, profile=profile)
        G = nx.Graph()
        for c in cards:
            G.add_node(
                c.id,
                nombre=c.nombre,
                numero=c.numero,
                tipo=c.tipo.value,
                elementos=c.elementos,
                mazo=c.mazo,
                color_hex=(c.colores.dominantes_hex[0] if c.colores.dominantes_hex else "#888888"),
            )

        # lista de vecinos candidatos por nodo
        scores: dict[str, list[tuple[str, float, SimilarityResult]]] = {c.id: [] for c in cards}
        for (a, b), res in pairs.items():
            s = self._score_for_layer(res, layer)
            scores[a].append((b, s, res))
            scores[b].append((a, s, res))

        edges_to_add: set[tuple[str, str]] = set()

        if strategy == "threshold":
            for (a, b), res in pairs.items():
                s = self._score_for_layer(res, layer)
                if s >= threshold:
                    edges_to_add.add(tuple(sorted((a, b))))
        else:
            neighbor_sets: dict[str, set[str]] = {}
            for node, neighs in scores.items():
                neighs_sorted = sorted(neighs, key=lambda x: -x[1])[:top_k]
                neighbor_sets[node] = {n for n, s, _res in neighs_sorted}
                for other, s, _res in neighs_sorted:
                    if strategy == "top_k" and not mutual_top_k:
                        edges_to_add.add(tuple(sorted((node, other))))
            if mutual_top_k or strategy == "mutual_top_k":
                edges_to_add = set()
                for node, sset in neighbor_sets.items():
                    for other in sset:
                        if node in neighbor_sets.get(other, set()):
                            edges_to_add.add(tuple(sorted((node, other))))

        now = datetime.now(timezone.utc).isoformat()
        for a, b in edges_to_add:
            res = pairs[(a, b)]
            s = self._score_for_layer(res, layer)
            G.add_edge(
                a,
                b,
                weight=s,
                similarity_total=res.similarity_total,
                dimensions=res.dimensions.model_dump(),
                contributions=res.contributions.model_dump(),
                explanation=res.explanation.model_dump(),
                profile=res.profile,
                layer=layer,
                model_version=self.model_version,
                computed_at=now,
                threshold=threshold,
            )

        logger.info(
            "Grafo layer=%s nodes=%s edges=%s strategy=%s",
            layer,
            G.number_of_nodes(),
            G.number_of_edges(),
            strategy,
        )
        return G

    def filter_graph(
        self,
        G: nx.Graph,
        *,
        mazo: str | None = None,
        tipo: str | None = None,
        elemento: str | None = None,
        min_weight: float | None = None,
        card_ids: list[str] | None = None,
    ) -> nx.Graph:
        nodes = list(G.nodes())
        if mazo:
            nodes = [n for n in nodes if G.nodes[n].get("mazo") == mazo]
        if tipo:
            nodes = [n for n in nodes if G.nodes[n].get("tipo") == tipo]
        if elemento:
            nodes = [n for n in nodes if elemento in (G.nodes[n].get("elementos") or [])]
        if card_ids:
            nodes = [n for n in nodes if n in set(card_ids)]
        H = G.subgraph(nodes).copy()
        if min_weight is not None:
            drop = [(u, v) for u, v, d in H.edges(data=True) if d.get("weight", 0) < min_weight]
            H.remove_edges_from(drop)
        return H


def edge_to_public(u: str, v: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"source": u, "target": v, **{k: data[k] for k in data}}
