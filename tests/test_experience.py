"""Tests de experiencias (historia, carta del día, puente, lámina)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.experience import (  # noqa: E402
    build_story,
    card_of_the_day,
    constellation_focus,
    export_lamina,
    make_bridge_challenge,
)


@pytest.fixture(scope="module")
def cards():
    return load_all_cards()


def test_story_mode(cards):
    ids = [cards[0].id, cards[1].id, cards[2].id]
    story = build_story(ids, cards=cards)
    assert story.opening
    assert story.closing
    assert story.alternate_ending_a
    assert len(story.questions) >= 1


def test_card_of_the_day_stable(cards):
    a = card_of_the_day(date(2026, 7, 14), cards=cards)
    b = card_of_the_day(date(2026, 7, 14), cards=cards)
    assert a["card"].id == b["card"].id
    assert a["pregunta"]


def test_bridge_challenge(cards):
    ch = make_bridge_challenge(cards=cards, seed="test-seed-1")
    assert ch.start_id != ch.end_id
    assert ch.answer_id in ch.options
    assert ch.answer_id not in {ch.start_id, ch.end_id}
    assert len(ch.path) >= 3


def test_export_lamina(cards):
    ids = [cards[0].id, cards[8].id, cards[16].id]
    png = export_lamina(ids, title="Test", subtitle="demo", story_lines=["hola"], cards=cards)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_constellation(cards):
    data = constellation_focus(cards[0].id, cards=cards, k=4)
    assert data["center"] == cards[0].id
    assert len(data["neighbors"]) <= 4
