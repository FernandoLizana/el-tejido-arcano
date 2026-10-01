"""Tests del pack Quien eres."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.personality_quiz import (  # noqa: E402
    QUESTIONS,
    birthdate_digit_sum,
    guide_card_from_birthdate,
    personal_spread_from_birthdate,
    score_quiz,
)


@pytest.fixture(scope="module")
def cards():
    return load_all_cards()


def test_quiz_scoring_is_deterministic(cards):
    answers = {q.id: q.options[0].id for q in QUESTIONS}
    first = score_quiz(answers, cards=cards)
    second = score_quiz(answers, cards=cards)

    assert first == second
    assert first.answered == len(QUESTIONS)
    assert first.primary_id.startswith("major_")
    assert 1 <= len(first.runner_up_ids) <= 3


def test_quiz_ignores_missing_answers(cards):
    result = score_quiz({}, cards=cards)

    assert result.answered == 0
    assert result.primary_id == "major_00_fool"


def test_birthdate_to_guide_card(cards):
    born = date(1990, 5, 17)
    result = guide_card_from_birthdate(born, cards=cards)

    assert birthdate_digit_sum(born) == 32
    assert result.index == 10
    assert result.card_id == "major_10_wheel_of_fortune"
    assert "32 mod 22 = 10" in result.explanation


def test_personal_spread_is_stable_permutation(cards):
    born = date(1990, 5, 17)
    spread_a = personal_spread_from_birthdate(born, cards=cards)
    spread_b = personal_spread_from_birthdate(born, cards=cards)
    ids = [p.card_id for p in spread_a.positions]

    assert spread_a == spread_b
    assert len(ids) == 22
    assert len(set(ids)) == 22
    assert {c.id for c in cards} == set(ids)


def test_personal_spread_quiz_modifier_highlights_card(cards):
    born = date(1990, 5, 17)
    plain = personal_spread_from_birthdate(born, cards=cards)
    modified = personal_spread_from_birthdate(born, cards=cards, quiz_card_id="major_17_star")

    assert [p.card_id for p in plain.positions] != [p.card_id for p in modified.positions]
    assert len({p.card_id for p in modified.positions}) == 22
    highlighted = [p for p in modified.positions if p.highlighted]
    assert len(highlighted) == 1
    assert highlighted[0].card_id == "major_17_star"
