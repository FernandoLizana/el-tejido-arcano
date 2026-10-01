"""Tests de juegos centrados en cartas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.games import cinema_spread, make_memory_round, make_odd_one_out, minute_oracle  # noqa: E402


@pytest.fixture(scope="module")
def cards():
    return load_all_cards()


def test_memory_pairs(cards):
    rnd = make_memory_round(cards, n_pairs=4, seed="mem-1")
    assert len(rnd.pairs) == 4
    assert len(rnd.tiles) == 8
    refs = [t["ref"] for t in rnd.tiles]
    assert len(set(refs)) == 4


def test_odd_one_out(cards):
    rnd = make_odd_one_out(cards, seed="odd-1")
    assert len(rnd.card_ids) == 4
    assert rnd.odd_id in rnd.card_ids


def test_minute_oracle_uses_card(cards):
    o = minute_oracle(cards, seed="ora-1")
    assert o.card.id
    assert o.dilema
    assert o.metafora


def test_cinema_spread(cards):
    cine = cinema_spread(cards=cards, seed="cine-1")
    assert len(cine.acts) == 3
    assert cine.acts[0]["role"] == "Arranque"


def test_cards_have_canseco_layer(cards):
    with_canseco = [c for c in cards if any("Canseco" in " ".join(s.autores) for s in c.significados)]
    assert len(with_canseco) == 22
