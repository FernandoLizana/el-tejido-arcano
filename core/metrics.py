"""Métricas de teoría de grafos + métricas propias del Tejido Arcano."""

from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Any, Iterable

import networkx as nx
import numpy as np

from schemas.card_schema import CardDNA

logger = logging.getLogger(__name__)


def safe_distance(similarity: float) -> float:
    return float(max(0.0, 1.0 - float(similarity)))


def graph_metrics(G: nx.Graph) -> dict[str, Any]:
    if G.number_of_nodes() == 0:
        return {"nodes": 0, "edges": 0}

    metrics: dict[str, Any] = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "degree": dict(G.degree()),
        "weighted_degree": dict(G.degree(weight="weight")),
    }

    try:
        metrics["betweenness"] = nx.betweenness_centrality(G, weight="weight")
    except Exception:  # noqa: BLE001
        metrics["betweenness"] = nx.betweenness_centrality(G)

    try:
        # usar distancia = 1-weight
        H = G.copy()
        for u, v, d in H.edges(data=True):
            d["dist"] = safe_distance(d.get("weight", 0))
        metrics["closeness"] = nx.closeness_centrality(H, distance="dist")
    except Exception:  # noqa: BLE001
        metrics["closeness"] = {}

    try:
        metrics["eigenvector"] = nx.eigenvector_centrality_numpy(G, weight="weight")
    except Exception:  # noqa: BLE001
        metrics["eigenvector"] = {}

    try:
        metrics["pagerank"] = nx.pagerank(G, weight="weight")
    except Exception:  # noqa: BLE001
        metrics["pagerank"] = {}

    metrics["clustering"] = nx.clustering(G, weight="weight")

    communities = detect_communities(G)
    metrics["communities"] = communities
    metrics["modularity"] = (
        nx.community.modularity(G, [set(c) for c in communities]) if communities else 0.0
    )

    if nx.is_connected(G):
        metrics["average_shortest_path_length"] = nx.average_shortest_path_length(G)
    else:
        largest = max(nx.connected_components(G), key=len)
        sub = G.subgraph(largest)
        metrics["average_shortest_path_length"] = (
            nx.average_shortest_path_length(sub) if sub.number_of_nodes() > 1 else 0.0
        )
        metrics["note"] = "Grafo no conexo; distancia media sobre componente mayor."

    # puentes y periferia
    try:
        metrics["bridges"] = [list(e) for e in nx.bridges(G)]
    except Exception:  # noqa: BLE001
        metrics["bridges"] = []

    deg = metrics["degree"]
    if deg:
        vals = list(deg.values())
        thr_low = sorted(vals)[max(0, len(vals) // 5)]
        thr_high = sorted(vals)[-max(1, len(vals) // 5)]
        metrics["peripheral_nodes"] = [n for n, d in deg.items() if d <= thr_low]
        metrics["central_nodes"] = [n for n, d in deg.items() if d >= thr_high]

    metrics["explanations"] = {
        "betweenness": (
            "La intermediación alta indica nodos que conectan comunidades distintas "
            "dentro de este modelo de datos y pesos, no una verdad universal del Tarot."
        ),
        "density": "Proporción de aristas presentes respecto al máximo posible en este grafo filtrado.",
    }
    return metrics


def detect_communities(G: nx.Graph, algorithm: str = "louvain") -> list[list[str]]:
    if G.number_of_nodes() == 0:
        return []
    try:
        if algorithm == "louvain":
            communities = nx.community.louvain_communities(G, weight="weight", seed=42)
            return [sorted(list(c)) for c in communities]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Louvain falló (%s); greedy modularity", exc)

    communities = nx.community.greedy_modularity_communities(G, weight="weight")
    return [sorted(list(c)) for c in communities]


def resonance_index(similarity_total: float) -> float:
    return float(np.clip(similarity_total, 0, 1))


def spread_density(G_sub: nx.Graph) -> dict[str, Any]:
    nodes = list(G_sub.nodes())
    n = len(nodes)
    if n < 2:
        return {
            "density": 0.0,
            "mean_similarity": 0.0,
            "min_similarity": 0.0,
            "max_similarity": 0.0,
            "strongest_pairs": [],
            "weakest_pairs": [],
        }
    weights = [d.get("weight", 0.0) for _, _, d in G_sub.edges(data=True)]
    # completa pares ausentes como 0 para densidad estructural
    possible = n * (n - 1) / 2
    dens = G_sub.number_of_edges() / possible if possible else 0.0
    pair_scores = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1 :]:
            if G_sub.has_edge(a, b):
                pair_scores.append((a, b, G_sub[a][b].get("weight", 0.0)))
            else:
                pair_scores.append((a, b, 0.0))
    sims = [s for _, _, s in pair_scores]
    strongest = sorted(pair_scores, key=lambda x: -x[2])[:3]
    weakest = sorted(pair_scores, key=lambda x: x[2])[:3]
    return {
        "density": dens,
        "mean_similarity": float(np.mean(sims)),
        "min_similarity": float(np.min(sims)),
        "max_similarity": float(np.max(sims)),
        "strongest_pairs": [{"a": a, "b": b, "score": s} for a, b, s in strongest],
        "weakest_pairs": [{"a": a, "b": b, "score": s} for a, b, s in weakest],
        "edge_weight_mean": float(np.mean(weights)) if weights else 0.0,
    }


def _entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    probs = [v / total for v in counts.values() if v > 0]
    if len(probs) <= 1:
        return 0.0
    h = -sum(p * math.log(p, 2) for p in probs)
    h_max = math.log(len(probs), 2)
    return float(np.clip(h / h_max if h_max else 0.0, 0.0, 1.0))


def symbolic_entropy(cards: list[CardDNA]) -> dict[str, float]:
    dims = {
        "elementos": Counter(e for c in cards for e in c.elementos),
        "simbolos": Counter(s for c in cards for s in c.simbolos),
        "emociones": Counter(e for c in cards for e in c.emociones),
        "arquetipos": Counter(a for c in cards for a in c.arquetipos),
        "palos": Counter(c.palo for c in cards if c.palo),
        "temperaturas": Counter(c.colores.temperatura_visual for c in cards),
    }
    return {k: _entropy(v) for k, v in dims.items()}


def bridge_card(G_sub: nx.Graph) -> dict[str, Any] | None:
    if G_sub.number_of_nodes() < 2:
        return None
    try:
        bet = nx.betweenness_centrality(G_sub, weight="weight")
    except Exception:  # noqa: BLE001
        bet = nx.betweenness_centrality(G_sub)
    # también similitud promedio
    avg_sim = {}
    for n in G_sub.nodes():
        weights = [d.get("weight", 0) for _, _, d in G_sub.edges(n, data=True)]
        avg_sim[n] = float(np.mean(weights)) if weights else 0.0
    score = {n: 0.6 * bet.get(n, 0) + 0.4 * avg_sim.get(n, 0) for n in G_sub.nodes()}
    best = max(score, key=score.get)
    return {
        "card_id": best,
        "score": score[best],
        "betweenness": bet.get(best, 0),
        "mean_similarity": avg_sim.get(best, 0),
        "note": (
            "Dentro de este modelo, esta carta podría explorarse como puente "
            "porque conecta mejor al resto del subgrafo de la tirada."
        ),
    }


def missing_patterns(cards: list[CardDNA], universe_elements: Iterable[str] | None = None) -> dict[str, list[str]]:
    universe_elements = list(universe_elements or ["fuego", "agua", "aire", "tierra"])
    present_el = set(e for c in cards for e in c.elementos)
    present_stages = set(s for c in cards for s in c.etapas_narrativas)
    present_emotions = set(e for c in cards for e in c.emociones)
    all_stages = {
        "inicio",
        "desarrollo",
        "conflicto",
        "crisis",
        "ruptura",
        "transformacion",
        "integracion",
        "resolucion",
    }
    return {
        "elementos_ausentes": sorted(set(universe_elements) - present_el),
        "etapas_ausentes": sorted(all_stages - present_stages),
        "emociones_presentes": sorted(present_emotions),
        "observation": (
            "Las ausencias son observaciones del conjunto seleccionado, "
            "no conclusiones absolutas sobre la situación."
        ),
    }


def archetypal_distance(G: nx.Graph, a: str, b: str) -> dict[str, Any]:
    if a not in G or b not in G:
        return {"distance": None, "path": [], "error": "nodo ausente"}
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d["dist"] = safe_distance(d.get("weight", 0))
    try:
        path = nx.shortest_path(H, a, b, weight="dist")
        dist = nx.shortest_path_length(H, a, b, weight="dist")
        return {"distance": dist, "path": path}
    except nx.NetworkXNoPath:
        return {"distance": None, "path": [], "error": "sin camino"}


def internal_tension(res_dims: dict[str, float], high: float = 0.65, low: float = 0.35) -> dict[str, Any]:
    highs = [k for k, v in res_dims.items() if v >= high]
    lows = [k for k, v in res_dims.items() if v <= low]
    score = 0.0
    if highs and lows:
        score = float(np.mean([res_dims[h] for h in highs]) * (1 - np.mean([res_dims[l] for l in lows])))
    return {
        "tension_score": score,
        "aligned_dimensions": highs,
        "opposed_dimensions": lows,
        "note": (
            "Una tensión alta puede explorarse como contraste interno: "
            "cercanía en unos ejes y alejamiento en otros."
        ),
    }


def narrative_coherence(cards: list[CardDNA]) -> list[str]:
    stages = [s for c in cards for s in c.etapas_narrativas]
    order = ["inicio", "llamada", "desarrollo", "conflicto", "crisis", "ruptura", "transformacion", "integracion", "resolucion", "cierre"]
    present = [s for s in order if s in stages]
    hyps = []
    if present:
        hyps.append(
            "Una hipótesis posible es leer la tirada como tránsito: "
            + " → ".join(present)
            + "."
        )
    else:
        hyps.append(
            "Dentro de este modelo, las etapas narrativas no forman una secuencia clara; "
            "puede explorarse como constelación temática más que como historia lineal."
        )
    elements = sorted({e for c in cards for e in c.elementos})
    if elements:
        hyps.append(
            f"Otra lectura posible enfatiza los elementos presentes ({', '.join(elements)}) "
            "como clima simbólico de la tirada."
        )
    return hyps
