"""Juegos centrados en las cartas del Tarot (entretenimiento reflexivo)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import Any

from core.card_repository import load_all_cards
from schemas.card_schema import CardDNA


def _rng(seed: str | None = None) -> random.Random:
    return random.Random(seed or date.today().isoformat())


def _jodo(card: CardDNA):
    for s in card.significados:
        if "Jodorowsky" in " ".join(s.autores) or "vía del Tarot" in s.fuente:
            return s
    return None


def _canseco(card: CardDNA):
    for s in card.significados:
        if "Canseco" in " ".join(s.autores) or "dilema a la metáfora" in s.fuente.lower():
            return s
    return None


def _prompt_words(card: CardDNA) -> str:
    j = _jodo(card)
    c = _canseco(card)
    if j and j.subtitulo:
        return j.subtitulo
    if c and c.esencia:
        return c.esencia
    if card.palabras_clave.luz:
        return ", ".join(card.palabras_clave.luz[:2])
    return card.nombre


@dataclass
class MemoryRound:
    pairs: list[tuple[str, str]]  # (card_id, clue)
    tiles: list[dict[str, str]]  # {id, kind: card|clue, ref, label}
    seed: str


def make_memory_round(cards: list[CardDNA] | None = None, n_pairs: int = 4, seed: str | None = None) -> MemoryRound:
    cards = cards or load_all_cards()
    rng = _rng(seed)
    chosen = rng.sample(cards, k=min(n_pairs, len(cards)))
    pairs = []
    tiles = []
    for c in chosen:
        clue = _prompt_words(c)
        pairs.append((c.id, clue))
        tiles.append({"id": f"card:{c.id}", "kind": "card", "ref": c.id, "label": c.nombre})
        tiles.append({"id": f"clue:{c.id}", "kind": "clue", "ref": c.id, "label": clue})
    rng.shuffle(tiles)
    return MemoryRound(pairs=pairs, tiles=tiles, seed=seed or date.today().isoformat())


@dataclass
class OddOneOutRound:
    card_ids: list[str]
    odd_id: str
    rule: str
    explanation: str
    seed: str


def make_odd_one_out(cards: list[CardDNA] | None = None, seed: str | None = None) -> OddOneOutRound:
    cards = cards or load_all_cards()
    rng = _rng(seed)
    # Prefer element-based rounds
    by_el: dict[str, list[CardDNA]] = {}
    for c in cards:
        for el in c.elementos or ["misterio"]:
            by_el.setdefault(el, []).append(c)
    eligible = [(el, lst) for el, lst in by_el.items() if len(lst) >= 3]
    if not eligible:
        raise RuntimeError("No hay elementos suficientes")
    el, group = rng.choice(eligible)
    three = rng.sample(group, 3)
    outsiders = [c for c in cards if el not in (c.elementos or [])]
    if not outsiders:
        outsiders = [c for c in cards if c.id not in {x.id for x in three}]
    odd = rng.choice(outsiders)
    ids = [c.id for c in three] + [odd.id]
    rng.shuffle(ids)
    return OddOneOutRound(
        card_ids=ids,
        odd_id=odd.id,
        rule=f"elemento «{el}»",
        explanation=(
            f"Tres cartas comparten el elemento {el}. "
            f"{odd.nombre} queda fuera en esta ronda."
        ),
        seed=seed or date.today().isoformat(),
    )


@dataclass
class MinuteOracle:
    card: CardDNA
    dilema: str
    metafora: str
    pregunta: str
    voz_jodorowsky: str
    voz_canseco: str
    cinematic: str
    disclaimer: str = (
        "Un minuto de metáfora, no de predicción. "
        "Usa la carta como espejo narrativo."
    )


def minute_oracle(cards: list[CardDNA] | None = None, seed: str | None = None) -> MinuteOracle:
    cards = cards or load_all_cards()
    rng = _rng(seed)
    card = rng.choice(cards)
    j = _jodo(card)
    c = _canseco(card)
    dilema = ""
    if c and c.preguntas:
        dilema = c.preguntas[0]
    elif j and j.preguntas:
        dilema = j.preguntas[0]
    else:
        dilema = f"¿Qué dilema pequeño me muestra {card.nombre} ahora?"

    metafora = (c.esencia if c and c.esencia else "") or (j.esencia if j and j.esencia else _prompt_words(card))
    pregunta = (j.preguntas[0] if j and j.preguntas else dilema)
    voz_j = (j.en_lectura if j and j.en_lectura else f"En la vía del Tarot, {card.nombre} invita a mirar {_prompt_words(card)}.")
    voz_c = (c.en_lectura if c and c.en_lectura else f"Como metáfora, {card.nombre} puede abrir una escena distinta de tu relato.")
    cinema = (c.en_lectura if c and c.en_lectura else f"Imagina {card.nombre} como el plano clave de una película íntima.")
    return MinuteOracle(
        card=card,
        dilema=dilema,
        metafora=metafora,
        pregunta=pregunta,
        voz_jodorowsky=voz_j,
        voz_canseco=voz_c,
        cinematic=cinema,
    )


@dataclass
class CinemaSpread:
    cards: list[CardDNA]
    acts: list[dict[str, str]]
    title: str
    alternate_cut: str
    disclaimer: str = (
        "Tirada-cine inspirada en la idea de contar con imágenes "
        "(Canseco / eco de Calvino): hipótesis narrativa, no destino."
    )


def cinema_spread(
    card_ids: list[str] | None = None,
    cards: list[CardDNA] | None = None,
    seed: str | None = None,
) -> CinemaSpread:
    cards = cards or load_all_cards()
    by_id = {c.id: c for c in cards}
    rng = _rng(seed)
    if card_ids and len(card_ids) >= 3:
        chosen = [by_id[i] for i in card_ids[:3]]
    else:
        chosen = rng.sample(cards, 3)

    roles = [
        ("Arranque", "La escena se enciende"),
        ("Conflicto", "Algo tensa el relato"),
        ("Corte final", "La cámara propone un cierre"),
    ]
    acts = []
    for card, (role, beat) in zip(chosen, roles):
        j = _jodo(card)
        c = _canseco(card)
        line = (c.en_lectura if c and c.en_lectura else "") or (j.esencia if j else "")
        if not line:
            line = f"{card.nombre} aporta {_prompt_words(card)}."
        acts.append(
            {
                "role": role,
                "beat": beat,
                "card_id": card.id,
                "card_name": card.nombre,
                "line": line,
                "metafora": (c.esencia if c else "") or (j.subtitulo if j else ""),
            }
        )

    title = " · ".join(a["card_name"] for a in acts)
    alt = (
        f"Corte alternativo: empieza en {chosen[2].nombre}, "
        f"el conflicto pasa por {chosen[0].nombre} y el eco final es {chosen[1].nombre}."
    )
    return CinemaSpread(cards=chosen, acts=acts, title=title, alternate_cut=alt)


def game_status() -> dict[str, Any]:
    return {
        "games": [
            "memory_arcano",
            "cual_no_encaja",
            "oraculo_un_minuto",
            "tirada_cine",
        ],
        "sources": ["Jodorowsky & Costa", "Miguel Ángel Díaz Canseco"],
        "focus": "cartas del tarot como imágenes-narrativas",
    }
