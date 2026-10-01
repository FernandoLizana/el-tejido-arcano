"""Tests del laboratorio multimodal (visión / texto / grafo)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.ml_lab import MultimodalLab, VisionIndex, extract_vision_vector  # noqa: E402


@pytest.fixture(scope="module")
def cards():
    data = load_all_cards()
    assert len(data) >= 5
    return data


def test_vision_vector_reproducible():
    img = ROOT / "cartas" / "la_torre.png"
    if not img.exists():
        pytest.skip("imagen ausente")
    a = extract_vision_vector(img)
    b = extract_vision_vector(img)
    assert a.shape == b.shape
    assert np.allclose(a, b)


def test_vision_neighbors(cards):
    idx = VisionIndex(pca_dim=12, seed=42)
    idx.fit(cards)
    assert len(idx.card_ids) == len(cards)
    neigh = idx.neighbors(cards[0].id, k=3)
    assert len(neigh) == 3
    assert all(0 <= s <= 1.01 for _, s in neigh)


def test_multimodal_recommend(cards):
    lab = MultimodalLab()
    lab.fit(cards)
    for mode in ("vision", "texto", "grafo", "combinado"):
        recs = lab.recommend(cards[0].id, mode=mode, k=3)  # type: ignore[arg-type]
        assert len(recs) == 3
        assert all(r.reasons for r in recs)


def test_multimodal_search(cards):
    lab = MultimodalLab()
    lab.fit(cards)
    hits = lab.search_meaning("liberacion", k=5)
    assert len(hits) >= 1
