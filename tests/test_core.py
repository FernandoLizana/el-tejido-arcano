"""Tests principales ArcanaGraph Lab."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.color_pipeline import (  # noqa: E402
    delta_e2000,
    extract_colors,
    palette_similarity,
    rgb_to_lab,
)
from core.graph_builder import GraphBuilder  # noqa: E402
from core.metrics import (  # noqa: E402
    bridge_card,
    missing_patterns,
    spread_density,
    symbolic_entropy,
)
from core.similarity_engine import SimilarityEngine, jaccard, validate_weights  # noqa: E402
from core.spread_analyzer import SpreadAnalyzer, find_hidden_path  # noqa: E402
from core.utils import load_similarity_config  # noqa: E402
from schemas.card_schema import CardDNA  # noqa: E402


@pytest.fixture(scope="module")
def cards():
    from core.card_repository import load_all_cards

    data = load_all_cards()
    assert len(data) >= 3
    return data


def test_validate_weights_sum():
    cfg = load_similarity_config()
    for name, weights in cfg["profiles"].items():
        validate_weights(weights)


def test_validate_weights_reject():
    with pytest.raises(ValueError):
        validate_weights({"color": 1.0, "symbols": 0, "semantic": 0, "archetypes": 0, "emotions": 0, "elements": 0, "numerology": 0, "narrative": 0.1})


def test_rgb_lab_delta_e_reproducible():
    lab1 = rgb_to_lab(np.array([[255, 0, 0]], dtype=float))[0]
    lab2 = rgb_to_lab(np.array([[0, 0, 255]], dtype=float))[0]
    d1 = delta_e2000(lab1, lab2)
    d2 = delta_e2000(lab1, lab2)
    assert d1 == d2
    assert d1 > 20


def test_color_extraction_reproducible():
    img = ROOT / "cartas" / "la_torre.png"
    if not img.exists():
        pytest.skip("imagen legacy ausente")
    a = extract_colors(img, k=3, seed=42)
    b = extract_colors(img, k=3, seed=42)
    assert a.rgb == b.rgb
    assert a.percentages == b.percentages


def test_palette_similarity_self_high():
    lab = [[50.0, 10.0, 10.0], [40.0, -5.0, 20.0]]
    pct = [0.6, 0.4]
    sim, _ = palette_similarity(lab, pct, lab, pct)
    assert sim > 0.95


def test_palette_similarity_opposite_lower():
    lab_a = [[80.0, 60.0, 50.0]]
    lab_b = [[20.0, -40.0, -40.0]]
    sim, _ = palette_similarity(lab_a, [1.0], lab_b, [1.0])
    assert sim < 0.5


def test_jaccard_symbols():
    assert jaccard(["torre", "rayo"], ["torre", "luna"]) == pytest.approx(1 / 3)


def test_card_schema_validation(cards):
    for c in cards:
        assert isinstance(c, CardDNA)
        assert c.id.startswith("major_")


def test_similarity_contributions_sum(cards):
    engine = SimilarityEngine(profile="equilibrado")
    engine.fit_corpus(cards)
    res = engine.compare(cards[0], cards[1])
    total = sum(res.contributions.model_dump().values())
    assert abs(total - res.similarity_total) < 1e-6
    assert 0 <= res.similarity_total <= 1


def test_graph_top_k(cards):
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", strategy="top_k", top_k=3)
    assert G.number_of_nodes() == len(cards)
    assert G.number_of_edges() > 0
    assert G.number_of_edges() < len(cards) * (len(cards) - 1) / 2


def test_mutual_top_k(cards):
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", strategy="mutual_top_k", top_k=2, mutual_top_k=True)
    assert G.number_of_nodes() == len(cards)


def test_communities(cards):
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", top_k=4)
    from core.metrics import graph_metrics

    m = graph_metrics(G)
    assert m["communities"]
    assert "betweenness" in m


def test_spread_analyzer(cards):
    ids = [cards[0].id, cards[1].id, cards[2].id]
    result = SpreadAnalyzer().analyze(ids, cards=cards)
    assert result.bridge_card is not None
    assert "density" in result.metrics
    assert "entropy" in result.metrics
    assert result.disclaimer


def test_symbolic_entropy(cards):
    ent = symbolic_entropy(cards[:5])
    assert all(0 <= v <= 1 for v in ent.values())


def test_missing_patterns(cards):
    miss = missing_patterns(cards[:3])
    assert "elementos_ausentes" in miss


def test_hidden_path(cards):
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", top_k=5)
    catalog = {c.id: c for c in cards}
    path = find_hidden_path(cards[0].id, cards[10].id, G, builder.engine, catalog, max_depth=5)
    assert path is not None
    assert path["sequence"][0] == cards[0].id
    assert path["sequence"][-1] == cards[10].id
    # no cycles
    assert len(path["sequence"]) == len(set(path["sequence"]))


def test_bridge_and_density(cards):
    import networkx as nx

    G = nx.Graph()
    a, b, c = cards[0].id, cards[1].id, cards[2].id
    G.add_nodes_from([a, b, c])
    G.add_edge(a, b, weight=0.8)
    G.add_edge(b, c, weight=0.7)
    G.add_edge(a, c, weight=0.2)
    dens = spread_density(G)
    assert dens["max_similarity"] >= dens["min_similarity"]
    br = bridge_card(G)
    assert br["card_id"] in {a, b, c}
