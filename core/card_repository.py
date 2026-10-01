"""Carga de cartas ADN desde JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from core.utils import get_root
from schemas.card_schema import CardDNA

logger = logging.getLogger(__name__)


def cards_dir() -> Path:
    return get_root() / "data" / "cards"


def load_card(path: Path) -> CardDNA:
    data = json.loads(path.read_text(encoding="utf-8"))
    return CardDNA.model_validate(data)


def load_all_cards(directory: Path | None = None) -> list[CardDNA]:
    d = directory or cards_dir()
    cards: list[CardDNA] = []
    for path in sorted(d.glob("*.json")):
        try:
            cards.append(load_card(path))
        except Exception as exc:  # noqa: BLE001
            logger.error("Error cargando %s: %s", path.name, exc)
            raise
    return cards


def index_cards(cards: list[CardDNA]) -> dict[str, CardDNA]:
    return {c.id: c for c in cards}


def get_card(card_id: str, cards: list[CardDNA] | None = None) -> CardDNA:
    catalog = index_cards(cards or load_all_cards())
    if card_id not in catalog:
        raise KeyError(f"Carta no encontrada: {card_id}")
    return catalog[card_id]
