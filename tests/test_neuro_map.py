"""Tests del mapa neurológico tarot ↔ regiones."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.neuro_map import (  # noqa: E402
    cards_for_region,
    explore_by_card,
    explore_by_region,
    load_card_links,
    load_regions,
    region_for_card,
)
from visualization.brain_3d import build_brain_figure  # noqa: E402


@pytest.fixture(scope="module")
def cards():
    return load_all_cards()


def test_regions_loaded():
    regs = load_regions()
    assert "prefrontal" in regs
    assert "hippocampus" in regs
    assert "imagination" in regs
    assert len(regs) >= 12


def test_all_majors_mapped(cards):
    links = load_card_links()
    assert len(links) == 22
    for c in cards:
        assert c.id in links
        assert links[c.id].primary in load_regions()


def test_explore_by_card(cards):
    fool = next(c for c in cards if c.id == "major_00_fool")
    info = explore_by_card(fool)
    assert info["primary"].id == "imagination"
    assert "disclaimer" in info


def test_explore_by_region(cards):
    info = explore_by_region("amygdala", cards)
    assert info["region"].id == "amygdala"
    ids = [x["card"].id for x in info["cards"]]
    assert "major_08_strength" in ids


def test_region_for_card():
    assert region_for_card("major_07_chariot").id == "motor"


def test_cards_for_region_nonempty():
    assert cards_for_region("prefrontal")


def test_brain_figure(cards):
    fig = build_brain_figure(cards, highlight_region="occipital")
    assert len(fig.data) >= 3
