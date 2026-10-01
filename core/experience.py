"""Experiencias atractivas: historia, carta del día, juego del puente, lámina."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from core.card_repository import load_all_cards
from core.graph_builder import GraphBuilder
from core.similarity_engine import SimilarityEngine
from core.spread_analyzer import SpreadAnalyzer, find_hidden_path
from core.utils import get_root
from schemas.card_schema import CardDNA

logger = logging.getLogger(__name__)

DISCLAIMER_SHORT = (
    "Hipótesis de este laboratorio. No es predicción ni consejo médico, legal o financiero."
)


def _image_path(card: CardDNA) -> Path | None:
    root = get_root()
    for p in (
        root / card.imagen,
        root / "cartas" / Path(card.imagen).name,
        root / "assets" / "cards" / "rws" / Path(card.imagen).name,
    ):
        if p.exists():
            return p
    return None


def _jodo(card: CardDNA) -> Any | None:
    for s in card.significados:
        if "vía del Tarot" in s.fuente or "Jodorowsky" in " ".join(s.autores):
            return s
    return card.significados[0] if card.significados else None


def _light_words(card: CardDNA, n: int = 3) -> str:
    words = list(card.palabras_clave.luz) or list(card.palabras_clave.neutrales) or card.arquetipos
    return ", ".join(words[:n]) if words else "un impulso aún sin nombre"


def _shadow_words(card: CardDNA, n: int = 2) -> str:
    words = list(card.palabras_clave.sombra) or card.emociones
    return ", ".join(words[:n]) if words else "una sombra no dicha"


@dataclass
class StoryModeResult:
    cards: list[str]
    title: str
    opening: str
    middle: str
    closing: str
    alternate_ending_a: str
    alternate_ending_b: str
    focus_pair: str
    tension_note: str
    questions: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER_SHORT


def build_story(
    card_ids: list[str],
    cards: list[CardDNA] | None = None,
    profile: str | None = None,
) -> StoryModeResult:
    """Genera una mini-historia reflexiva a partir de 2–3 cartas."""
    catalog = {c.id: c for c in (cards or load_all_cards())}
    selected = [catalog[i] for i in card_ids if i in catalog]
    if len(selected) < 2:
        raise ValueError("Se necesitan al menos 2 cartas")

    analyzer = SpreadAnalyzer()
    analysis = analyzer.analyze([c.id for c in selected], cards=list(catalog.values()), profile=profile)

    a, b = selected[0], selected[1]
    c = selected[2] if len(selected) > 2 else None

    ja, jb = _jodo(a), _jodo(b)
    jc = _jodo(c) if c else None

    title = f"{a.nombre} → {b.nombre}" + (f" → {c.nombre}" if c else "")

    opening = (
        f"Podría comenzar con **{a.nombre}**: {_light_words(a)}. "
        f"{(ja.esencia if ja and ja.esencia else 'Aparece como un primer movimiento del alma.')}"
    )

    middle = (
        f"Entonces entra **{b.nombre}**, donde también late {_light_words(b)} "
        f"y, en sombra, {_shadow_words(b)}. "
        f"{(jb.en_lectura if jb and jb.en_lectura else 'Esta segunda carta puede cambiar el clima de la lectura.')}"
    )

    if c:
        closing = (
            f"Una hipótesis de cierre pasa por **{c.nombre}**: {_light_words(c)}. "
            f"{(jc.esencia if jc and jc.esencia else '')} "
            f"Dentro de este modelo, el trío invita a mirar el tránsito, no a fijar un destino."
        )
        alt_a = (
            f"Otra lectura posible: **{a.nombre}** como llamada, **{c.nombre}** como respuesta, "
            f"y **{b.nombre}** como el puente emocional entre ambas."
        )
        alt_b = (
            f"También puede explorarse al revés: lo que parece resolución en **{c.nombre}** "
            f"aún carga la tensión abierta entre **{a.nombre}** y **{b.nombre}**."
        )
    else:
        closing = (
            f"Entre **{a.nombre}** y **{b.nombre}** puede leerse un diálogo: "
            f"no una sentencia, sino una conversación interior."
        )
        alt_a = f"Variante luminosa: enfatizar {_light_words(a)} encontrándose con {_light_words(b)}."
        alt_b = f"Variante sombría: escuchar {_shadow_words(a)} frente a {_shadow_words(b)}, con cuidado y sin fatalismo."

    focus = ""
    if analysis.strongest_pair:
        sp = analysis.strongest_pair
        names = {x.id: x.nombre for x in selected}
        focus = f"El vínculo más claro aquí aparece entre {names.get(sp['a'], sp['a'])} y {names.get(sp['b'], sp['b'])}."

    tension = ""
    if analysis.tension_pair:
        tp = analysis.tension_pair
        names = {x.id: x.nombre for x in selected}
        tension = (
            f"Hay un contraste interesante entre {names.get(tp['a'], tp['a'])} y "
            f"{names.get(tp['b'], tp['b'])}: se acercan en unos ejes y se alejan en otros."
        )

    questions: list[str] = []
    for card in selected:
        j = _jodo(card)
        if j and j.preguntas:
            questions.append(j.preguntas[0])
        elif card.palabras_clave.luz:
            questions.append(f"¿Dónde vivo hoy la calidad de «{card.palabras_clave.luz[0]}»?")
    questions = questions[:4] or [
        "¿Qué parte de esta historia me toca sin forzarme a creerla?",
        "¿Qué pequeño gesto podría responder a esta configuración?",
    ]

    for h in analysis.narrative_hypotheses[:1]:
        if h and h not in (opening, middle, closing):
            middle = middle + " " + h

    return StoryModeResult(
        cards=[c.id for c in selected],
        title=title,
        opening=opening,
        middle=middle,
        closing=closing,
        alternate_ending_a=alt_a,
        alternate_ending_b=alt_b,
        focus_pair=focus,
        tension_note=tension,
        questions=questions,
    )


def card_of_the_day(day: date | None = None, cards: list[CardDNA] | None = None) -> dict[str, Any]:
    """Carta estable por fecha (misma carta todo el día)."""
    day = day or date.today()
    cards = cards or load_all_cards()
    digest = hashlib.sha256(day.isoformat().encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(cards)
    card = cards[idx]
    j = _jodo(card)
    # companion: strongest semantic/visual neighbor via engine
    engine = SimilarityEngine(profile="equilibrado")
    engine.fit_corpus(cards)
    best = None
    best_score = -1.0
    for other in cards:
        if other.id == card.id:
            continue
        res = engine.compare(card, other)
        if res.similarity_total > best_score:
            best_score = res.similarity_total
            best = other
    return {
        "date": day.isoformat(),
        "card": card,
        "companion": best,
        "companion_score": best_score,
        "esencia": (j.esencia if j else ""),
        "subtitulo": (j.subtitulo if j else ""),
        "pregunta": (j.preguntas[0] if j and j.preguntas else f"¿Qué me muestra {card.nombre} hoy, con suavidad?"),
        "disclaimer": DISCLAIMER_SHORT,
    }


@dataclass
class BridgeChallenge:
    start_id: str
    end_id: str
    answer_id: str
    options: list[str]
    path: list[str]
    seed: str


def make_bridge_challenge(
    cards: list[CardDNA] | None = None,
    seed: str | None = None,
    profile: str | None = None,
) -> BridgeChallenge:
    """Elige dos cartas y una intermedia real del camino oculto."""
    import random

    cards = cards or load_all_cards()
    seed = seed or date.today().isoformat()
    rng = random.Random(seed)
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", profile=profile, top_k=5)
    catalog = {c.id: c for c in cards}

    # Prefer paths of length 3 (start-bridge-end)
    candidates: list[tuple[str, str, list[str]]] = []
    ids = [c.id for c in cards]
    rng.shuffle(ids)
    for a in ids[:12]:
        for b in ids:
            if a == b:
                continue
            path = find_hidden_path(a, b, G, builder.engine, catalog, profile=profile, max_depth=3)
            if path and len(path["sequence"]) == 3:
                candidates.append((a, b, path["sequence"]))
        if len(candidates) >= 8:
            break

    if not candidates:
        # fallback: any path length 3-4
        for a in ids:
            for b in ids:
                if a >= b:
                    continue
                path = find_hidden_path(a, b, G, builder.engine, catalog, profile=profile, max_depth=4)
                if path and len(path["sequence"]) >= 3:
                    candidates.append((a, b, path["sequence"]))
                    break
            if candidates:
                break

    if not candidates:
        raise RuntimeError("No se pudo armar un reto de puente con el grafo actual")

    start, end, sequence = rng.choice(candidates)
    # pick a middle node as answer
    middles = sequence[1:-1]
    answer = rng.choice(middles)
    distractors = [c.id for c in cards if c.id not in {start, end, answer}]
    options = [answer] + rng.sample(distractors, k=min(3, len(distractors)))
    rng.shuffle(options)
    return BridgeChallenge(
        start_id=start,
        end_id=end,
        answer_id=answer,
        options=options,
        path=sequence,
        seed=seed,
    )


def export_lamina(
    card_ids: list[str],
    title: str = "Tirada — El Tejido Arcano",
    subtitle: str = "",
    story_lines: list[str] | None = None,
    cards: list[CardDNA] | None = None,
) -> bytes:
    """Exporta una lámina PNG horizontal legible."""
    catalog = {c.id: c for c in (cards or load_all_cards())}
    selected = [catalog[i] for i in card_ids if i in catalog]
    if not selected:
        raise ValueError("Sin cartas para exportar")

    card_w, card_h = 220, 360
    margin = 36
    gap = 24
    footer_h = 160
    header_h = 110
    width = margin * 2 + len(selected) * card_w + (len(selected) - 1) * gap
    width = max(width, 720)
    height = header_h + card_h + footer_h + margin

    bg = (18, 18, 24)
    ink = (236, 230, 220)
    mute = (170, 162, 150)
    accent = (196, 160, 90)

    canvas = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(canvas)
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_body = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = font_title
        font_small = font_title

    draw.text((margin, 28), title, fill=ink, font=font_title)
    if subtitle:
        draw.text((margin, 68), subtitle[:90], fill=mute, font=font_body)
    draw.line((margin, header_h - 18, width - margin, header_h - 18), fill=accent, width=2)

    x = margin
    y = header_h
    for card in selected:
        path = _image_path(card)
        if path:
            im = Image.open(path).convert("RGB")
            im.thumbnail((card_w, card_h))
            # center in slot
            ox = x + (card_w - im.width) // 2
            oy = y + (card_h - im.height) // 2
            canvas.paste(im, (ox, oy))
        draw.text((x, y + card_h + 8), card.nombre, fill=ink, font=font_body)
        x += card_w + gap

    fy = y + card_h + 40
    lines = story_lines or []
    wrapped: list[str] = []
    for line in lines:
        # crude wrap
        words = line.split()
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) > 95:
                wrapped.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            wrapped.append(cur)
    for i, line in enumerate(wrapped[:5]):
        draw.text((margin, fy + i * 20), line, fill=mute, font=font_small)

    draw.text(
        (margin, height - 28),
        DISCLAIMER_SHORT,
        fill=(120, 114, 108),
        font=font_small,
    )

    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def constellation_focus(
    card_id: str,
    cards: list[CardDNA] | None = None,
    profile: str | None = None,
    k: int = 5,
) -> dict[str, Any]:
    """Subgrafo local alrededor de una carta, con razones."""
    cards = cards or load_all_cards()
    builder = GraphBuilder()
    G = builder.build(cards, layer="combined", profile=profile, top_k=max(k, 4))
    if card_id not in G:
        raise KeyError(card_id)
    engine = builder.engine
    catalog = {c.id: c for c in cards}
    neighbors = sorted(
        ((n, G[card_id][n].get("weight", 0.0), G[card_id][n]) for n in G.neighbors(card_id)),
        key=lambda x: -x[1],
    )[:k]
    details = []
    for nid, w, data in neighbors:
        exp = data.get("explanation") or {}
        if not exp:
            res = engine.compare(catalog[card_id], catalog[nid], profile=profile)
            exp = res.explanation.model_dump()
            dims = res.dimensions.model_dump()
        else:
            dims = data.get("dimensions") or {}
        top_dims = sorted(dims.items(), key=lambda x: -x[1])[:3] if dims else []
        details.append(
            {
                "id": nid,
                "nombre": catalog[nid].nombre,
                "score": w,
                "shared_symbols": exp.get("shared_symbols") or [],
                "shared_emotions": exp.get("shared_emotions") or [],
                "top_dimensions": top_dims,
                "differences": (exp.get("main_differences") or [])[:2],
            }
        )
    return {
        "center": card_id,
        "center_name": catalog[card_id].nombre,
        "neighbors": details,
        "disclaimer": DISCLAIMER_SHORT,
    }
