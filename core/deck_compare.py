"""Stub comparador de mazos — arquitectura lista para Marsella/otros."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from schemas.card_schema import CardDNA


@dataclass
class DeckCompareResult:
    card_a: str
    card_b: str
    same_number: bool
    color_delta_notes: list[str]
    symbols_added: list[str]
    symbols_removed: list[str]
    semantic_score: float | None
    notes: list[str]


def compare_same_arcana(a: CardDNA, b: CardDNA) -> DeckCompareResult:
    """Compara la 'misma' carta entre mazos (por numero + tipo)."""
    sa, sb = set(a.simbolos), set(b.simbolos)
    return DeckCompareResult(
        card_a=a.id,
        card_b=b.id,
        same_number=a.numero == b.numero and a.tipo == b.tipo,
        color_delta_notes=[
            f"temperatura {a.colores.temperatura_visual} vs {b.colores.temperatura_visual}"
        ],
        symbols_added=sorted(sb - sa),
        symbols_removed=sorted(sa - sb),
        semantic_score=None,
        notes=[
            "Comparador experimental: requiere ADN anotado por mazo.",
            "No interpreta diferencias como superioridad de un mazo.",
        ],
    )


def to_dict(result: DeckCompareResult) -> dict[str, Any]:
    return result.__dict__
