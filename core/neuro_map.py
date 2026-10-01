"""Mapa analógico Tarot ↔ regiones cerebrales (educativo, no clínico)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from schemas.card_schema import CardDNA

ROOT = Path(__file__).resolve().parent.parent
NEURO_DIR = ROOT / "data" / "sources" / "neuro"


@dataclass
class BrainRegion:
    id: str
    nombre: str
    sistema: str
    color: str
    xyz: tuple[float, float, float]
    hecho_breve: str
    detalle: str


@dataclass
class CardBrainLink:
    card_id: str
    primary: str
    secondary: list[str]
    rationale: str
    pregunta: str


@lru_cache(maxsize=1)
def load_regions() -> dict[str, BrainRegion]:
    data = json.loads((NEURO_DIR / "regions.json").read_text(encoding="utf-8"))
    out: dict[str, BrainRegion] = {}
    for r in data["regions"]:
        xyz = tuple(float(x) for x in r["xyz"])
        out[r["id"]] = BrainRegion(
            id=r["id"],
            nombre=r["nombre"],
            sistema=r["sistema"],
            color=r["color"],
            xyz=(xyz[0], xyz[1], xyz[2]),  # type: ignore[assignment]
            hecho_breve=r["hecho_breve"],
            detalle=r["detalle"],
        )
    return out


@lru_cache(maxsize=1)
def load_card_links() -> dict[str, CardBrainLink]:
    data = json.loads((NEURO_DIR / "card_brain_map.json").read_text(encoding="utf-8"))
    out: dict[str, CardBrainLink] = {}
    for cid, m in data["mappings"].items():
        out[cid] = CardBrainLink(
            card_id=cid,
            primary=m["primary"],
            secondary=list(m.get("secondary") or []),
            rationale=m["rationale"],
            pregunta=m.get("pregunta", ""),
        )
    return out


def map_disclaimer() -> str:
    data = json.loads((NEURO_DIR / "card_brain_map.json").read_text(encoding="utf-8"))
    return data.get("disclaimer", "")


def source_notes() -> dict[str, Any]:
    data = json.loads((NEURO_DIR / "regions.json").read_text(encoding="utf-8"))
    return data.get("source_notes", {})


def _jodo_canseco_blurbs(card: CardDNA) -> tuple[str, str]:
    jodo, canseco = "", ""
    for s in card.significados:
        autores = " ".join(s.autores)
        if "Jodorowsky" in autores or "vía del Tarot" in s.fuente:
            jodo = (s.subtitulo or s.esencia or "")[:280]
        if "Canseco" in autores or "dilema" in s.fuente.lower():
            canseco = (s.esencia or s.subtitulo or "")[:280]
    return jodo, canseco


def region_for_card(card_id: str) -> BrainRegion | None:
    links = load_card_links()
    regions = load_regions()
    link = links.get(card_id)
    if not link:
        return None
    return regions.get(link.primary)


def cards_for_region(region_id: str) -> list[str]:
    links = load_card_links()
    primary = [cid for cid, L in links.items() if L.primary == region_id]
    secondary = [
        cid
        for cid, L in links.items()
        if region_id in L.secondary and cid not in primary
    ]
    return primary + secondary


def explore_by_card(card: CardDNA) -> dict[str, Any]:
    links = load_card_links()
    regions = load_regions()
    link = links.get(card.id)
    if not link:
        return {"error": "Sin mapeo neurológico para esta carta."}
    primary = regions[link.primary]
    secondary = [regions[r] for r in link.secondary if r in regions]
    jodo, canseco = _jodo_canseco_blurbs(card)
    return {
        "card_id": card.id,
        "card_nombre": card.nombre,
        "primary": primary,
        "secondary": secondary,
        "rationale": link.rationale,
        "pregunta": link.pregunta,
        "voz_jodorowsky": jodo,
        "voz_canseco": canseco,
        "disclaimer": map_disclaimer(),
    }


def explore_by_region(region_id: str, cards: list[CardDNA]) -> dict[str, Any]:
    regions = load_regions()
    region = regions.get(region_id)
    if not region:
        return {"error": f"Región desconocida: {region_id}"}
    by_id = {c.id: c for c in cards}
    ids = cards_for_region(region_id)
    linked = []
    links = load_card_links()
    for cid in ids:
        c = by_id.get(cid)
        if not c:
            continue
        L = links[cid]
        role = "principal" if L.primary == region_id else "resonante"
        linked.append(
            {
                "card": c,
                "role": role,
                "rationale": L.rationale,
                "pregunta": L.pregunta,
            }
        )
    return {
        "region": region,
        "cards": linked,
        "disclaimer": map_disclaimer(),
        "sources": source_notes(),
    }


def all_region_ids() -> list[str]:
    return list(load_regions().keys())
