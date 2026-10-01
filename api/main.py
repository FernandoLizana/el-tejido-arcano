"""API FastAPI — ArcanaGraph Lab."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.card_repository import get_card, load_all_cards  # noqa: E402
from core.graph_builder import GraphBuilder  # noqa: E402
from core.metrics import graph_metrics  # noqa: E402
from core.ml_lab import MultimodalLab  # noqa: E402
from core.similarity_engine import SimilarityEngine  # noqa: E402
from core.spread_analyzer import SpreadAnalyzer, find_hidden_path  # noqa: E402
from core.utils import load_pipeline_config, load_similarity_config  # noqa: E402

app = FastAPI(
    title="ArcanaGraph Lab API",
    description=(
        "API experimental del Tejido Arcano. Las métricas describen el modelo y "
        "los datos configurados; no constituyen predicciones ni verdades universales."
    ),
    version="1.0.0-iter1",
)

DISCLAIMER = (
    "Herramienta experimental de estudio simbólico. No sustituye atención médica, "
    "psicológica, legal o financiera."
)


class CompareRequest(BaseModel):
    card_a: str
    card_b: str
    profile: str | None = None


class SpreadRequest(BaseModel):
    cards: list[str] = Field(..., min_length=1, max_length=12)
    profile: str | None = None


class PathRequest(BaseModel):
    card_a: str
    card_b: str
    profile: str | None = None
    max_depth: int = 4
    mode: str = "max_similarity"


class MLRecommendRequest(BaseModel):
    card_id: str
    mode: str = "combinado"  # vision | texto | grafo | combinado
    k: int = Field(default=5, ge=1, le=15)


class MLSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(default=8, ge=1, le=20)


class SettingsUpdate(BaseModel):
    profile: str | None = None
    top_k: int | None = None
    threshold: float | None = None


_builder: GraphBuilder | None = None
_graph_cache: dict[str, Any] = {}
_ml_lab: MultimodalLab | None = None


def builder() -> GraphBuilder:
    global _builder
    if _builder is None:
        _builder = GraphBuilder()
    return _builder


def ml_lab() -> MultimodalLab:
    global _ml_lab
    if _ml_lab is None:
        _ml_lab = MultimodalLab()
        _ml_lab.fit(load_all_cards())
    return _ml_lab


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": DISCLAIMER}


@app.get("/api/cards")
def list_cards() -> list[dict[str, Any]]:
    cards = load_all_cards()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "numero": c.numero,
            "tipo": c.tipo.value,
            "mazo": c.mazo,
            "elementos": c.elementos,
        }
        for c in cards
    ]


@app.get("/api/cards/{card_id}")
def card_detail(card_id: str) -> dict[str, Any]:
    try:
        return get_card(card_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/cards/{card_id}/neighbors")
def card_neighbors(card_id: str, layer: str = "combined", k: int = 4) -> dict[str, Any]:
    cards = load_all_cards()
    G = builder().build(cards, layer=layer)  # type: ignore[arg-type]
    if card_id not in G:
        raise HTTPException(404, f"Carta ausente en grafo: {card_id}")
    neigh = sorted(
        ((n, G[card_id][n].get("weight", 0)) for n in G.neighbors(card_id)),
        key=lambda x: -x[1],
    )[:k]
    return {"card_id": card_id, "neighbors": [{"id": n, "weight": w} for n, w in neigh]}


@app.get("/api/cards/{card_id}/metrics")
def card_metrics(card_id: str, layer: str = "combined") -> dict[str, Any]:
    cards = load_all_cards()
    G = builder().build(cards, layer=layer)  # type: ignore[arg-type]
    m = graph_metrics(G)
    if card_id not in G:
        raise HTTPException(404, "Carta no encontrada")
    return {
        "card_id": card_id,
        "degree": m["degree"].get(card_id),
        "betweenness": m.get("betweenness", {}).get(card_id),
        "closeness": m.get("closeness", {}).get(card_id),
        "pagerank": m.get("pagerank", {}).get(card_id),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/graph")
def get_graph(layer: str = "combined", profile: str | None = None) -> dict[str, Any]:
    key = f"{layer}:{profile or 'default'}"
    cards = load_all_cards()
    G = builder().build(cards, layer=layer, profile=profile)  # type: ignore[arg-type]
    _graph_cache[key] = G
    return {
        "layer": layer,
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes()],
        "edges": [
            {"source": u, "target": v, "weight": d.get("weight"), "dimensions": d.get("dimensions")}
            for u, v, d in G.edges(data=True)
        ],
        "model_version": load_pipeline_config().get("model_version"),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/graph/communities")
def communities(layer: str = "combined") -> dict[str, Any]:
    cards = load_all_cards()
    G = builder().build(cards, layer=layer)  # type: ignore[arg-type]
    m = graph_metrics(G)
    return {"communities": m.get("communities"), "modularity": m.get("modularity"), "disclaimer": DISCLAIMER}


@app.post("/api/compare")
def compare(req: CompareRequest) -> dict[str, Any]:
    try:
        a = get_card(req.card_a)
        b = get_card(req.card_b)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    engine = SimilarityEngine(profile=req.profile)
    engine.fit_corpus(load_all_cards())
    return engine.compare(a, b, profile=req.profile).model_dump(mode="json")


@app.post("/api/spreads/analyze")
def analyze_spread(req: SpreadRequest) -> dict[str, Any]:
    try:
        result = SpreadAnalyzer(builder()).analyze(req.cards, profile=req.profile)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/api/paths/hidden")
def hidden_path(req: PathRequest) -> dict[str, Any]:
    cards = load_all_cards()
    G = builder().build(cards, layer="combined", profile=req.profile)
    catalog = {c.id: c for c in cards}
    path = find_hidden_path(
        req.card_a,
        req.card_b,
        G,
        builder().engine,
        catalog,
        profile=req.profile,
        max_depth=req.max_depth,
        mode=req.mode,  # type: ignore[arg-type]
    )
    if not path:
        raise HTTPException(404, "No se encontró camino con los parámetros dados")
    return path


@app.get("/api/taxonomies")
def taxonomies() -> dict[str, Any]:
    import json

    out = {}
    for p in (ROOT / "data" / "taxonomies").glob("*.json"):
        out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out


@app.get("/api/settings")
def settings() -> dict[str, Any]:
    return {
        "pipeline": load_pipeline_config(),
        "similarity": load_similarity_config(),
        "disclaimer": DISCLAIMER,
    }


@app.put("/api/settings")
def update_settings(body: SettingsUpdate) -> dict[str, Any]:
    # En iteración 1: aplica en memoria al builder
    b = builder()
    if body.profile:
        b.engine.set_profile(body.profile)
    if body.top_k is not None:
        b.top_k = body.top_k
    if body.threshold is not None:
        b.threshold = body.threshold
    return {"ok": True, "settings": {"profile": b.engine.default_profile, "top_k": b.top_k, "threshold": b.threshold}}


@app.post("/api/rebuild-graph")
def rebuild() -> dict[str, Any]:
    cards = load_all_cards()
    layers = ["color", "semantic", "combined"]
    summary = {}
    for layer in layers:
        G = builder().build(cards, layer=layer)  # type: ignore[arg-type]
        summary[layer] = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
    return {"summary": summary, "disclaimer": DISCLAIMER}


@app.post("/api/ml/recommend")
def ml_recommend(req: MLRecommendRequest) -> dict[str, Any]:
    if req.mode not in {"vision", "texto", "grafo", "combinado"}:
        raise HTTPException(400, "mode inválido")
    try:
        get_card(req.card_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    recs = ml_lab().recommend(req.card_id, mode=req.mode, k=req.k)  # type: ignore[arg-type]
    return {
        "card_id": req.card_id,
        "mode": req.mode,
        "recommendations": [
            {"card_id": r.card_id, "score": r.score, "reasons": r.reasons} for r in recs
        ],
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/ml/search")
def ml_search(req: MLSearchRequest) -> dict[str, Any]:
    hits = ml_lab().search_meaning(req.query, k=req.k)
    return {
        "query": req.query,
        "results": [{"card_id": r.card_id, "score": r.score, "reasons": r.reasons} for r in hits],
        "disclaimer": DISCLAIMER,
    }
