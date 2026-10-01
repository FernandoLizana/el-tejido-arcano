"""Motor de similitud multidimensional explicable."""

from __future__ import annotations

import logging
from typing import Iterable

import numpy as np

from core.color_pipeline import palette_similarity
from core.embeddings import EmbeddingCache, EmbeddingProvider, get_provider
from core.utils import get_root, load_pipeline_config, load_similarity_config, stable_hash
from schemas.card_schema import (
    CardDNA,
    DimensionScores,
    SimilarityExplanation,
    SimilarityResult,
)

logger = logging.getLogger(__name__)


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(x.lower().strip() for x in a if x), set(y.lower().strip() for y in b if y)
    if not sa and not sb:
        return 0.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def validate_weights(weights: dict[str, float], tol: float = 1e-6) -> dict[str, float]:
    expected = [
        "color",
        "symbols",
        "semantic",
        "archetypes",
        "emotions",
        "elements",
        "numerology",
        "narrative",
    ]
    missing = [k for k in expected if k not in weights]
    if missing:
        raise ValueError(f"Pesos incompletos, faltan: {missing}")
    total = sum(float(weights[k]) for k in expected)
    if abs(total - 1.0) > tol:
        raise ValueError(f"Los pesos deben sumar 1.0 (suma={total})")
    return {k: float(weights[k]) for k in expected}


def card_semantic_text(card: CardDNA) -> str:
    pk = card.palabras_clave
    sig_parts: list[str] = []
    for s in card.significados:
        sig_parts.extend(
            [
                s.esencia,
                s.subtitulo,
                s.en_lectura,
                " ".join(s.preguntas),
                " ".join(s.palabras_luz),
                " ".join(s.palabras_sombra),
                " ".join(s.palabras_neutrales),
            ]
        )
    parts = [
        card.nombre,
        card.nombre_original,
        " ".join(pk.neutrales),
        " ".join(pk.luz),
        " ".join(pk.sombra),
        " ".join(card.arquetipos),
        " ".join(card.emociones),
        " ".join(card.etapas_narrativas),
        " ".join(card.simbolos),
        " ".join(card.elementos),
        " ".join(sig_parts),
    ]
    return " | ".join(p for p in parts if p)


class SimilarityEngine:
    def __init__(
        self,
        profile: str | None = None,
        provider: EmbeddingProvider | None = None,
        model_version: str | None = None,
    ) -> None:
        sim_cfg = load_similarity_config()
        pipe = load_pipeline_config()
        self.profiles = sim_cfg["profiles"]
        self.default_profile = profile or sim_cfg.get("default_profile", "equilibrado")
        self.weights = validate_weights(self.profiles[self.default_profile])
        self.provider = provider or get_provider(pipe.get("embedding_provider", "tfidf"))
        self.model_version = model_version or pipe.get("model_version", "1.0.0-iter1")
        self.cache = EmbeddingCache(get_root() / "data" / "cache" / "embeddings")
        self._corpus_fitted = False
        self._embedding_index: dict[str, np.ndarray] = {}

    def set_profile(self, profile: str) -> None:
        if profile not in self.profiles:
            raise KeyError(f"Perfil desconocido: {profile}")
        self.default_profile = profile
        self.weights = validate_weights(self.profiles[profile])

    def fit_corpus(self, cards: list[CardDNA]) -> None:
        texts = [card_semantic_text(c) for c in cards]
        vectors = self.provider.embed(texts)
        if getattr(self.provider, "name", "") == "tfidf" and hasattr(self.provider, "fit"):
            # already fitted inside embed
            pass
        for card, vec in zip(cards, vectors):
            ch = stable_hash(card.content_hash_payload())
            cached = self.cache.load(card.id, ch, self.provider.name)
            if cached is not None:
                self._embedding_index[card.id] = cached
            else:
                self._embedding_index[card.id] = np.asarray(vec, dtype=float)
                self.cache.save(card.id, ch, self.provider.name, self._embedding_index[card.id])
        self._corpus_fitted = True
        logger.info("Corpus semántico indexado: %s cartas", len(cards))

    def _get_embedding(self, card: CardDNA) -> np.ndarray:
        if card.id in self._embedding_index:
            return self._embedding_index[card.id]
        ch = stable_hash(card.content_hash_payload())
        cached = self.cache.load(card.id, ch, self.provider.name)
        if cached is not None:
            self._embedding_index[card.id] = cached
            return cached
        vec = self.provider.embed([card_semantic_text(card)])[0]
        self._embedding_index[card.id] = np.asarray(vec, dtype=float)
        self.cache.save(card.id, ch, self.provider.name, self._embedding_index[card.id])
        return self._embedding_index[card.id]

    def compare(self, a: CardDNA, b: CardDNA, profile: str | None = None) -> SimilarityResult:
        if profile:
            weights = validate_weights(self.profiles[profile])
            profile_name = profile
        else:
            weights = self.weights
            profile_name = self.default_profile

        color_sim, color_notes = palette_similarity(
            a.colores.dominantes_lab,
            a.colores.porcentajes or [1.0 / max(len(a.colores.dominantes_lab), 1)] * len(a.colores.dominantes_lab),
            b.colores.dominantes_lab,
            b.colores.porcentajes or [1.0 / max(len(b.colores.dominantes_lab), 1)] * len(b.colores.dominantes_lab),
        )
        if not a.colores.dominantes_lab and not b.colores.dominantes_lab:
            color_sim = 0.0

        symbols = jaccard(a.simbolos, b.simbolos)
        archetypes = jaccard(a.arquetipos, b.arquetipos)
        emotions = jaccard(a.emociones, b.emociones)
        elements = jaccard(a.elementos, b.elementos)
        narrative = jaccard(a.etapas_narrativas, b.etapas_narrativas)

        # numerología: cercanía de número y reducción
        if a.numerologia and b.numerologia:
            dn = abs(a.numerologia.numero - b.numerologia.numero) / 22.0
            dr = abs(a.numerologia.reduccion - b.numerologia.reduccion) / 9.0
            numerology = float(np.clip(1.0 - 0.6 * dn - 0.4 * dr, 0, 1))
        else:
            numerology = 0.0

        ea, eb = self._get_embedding(a), self._get_embedding(b)
        semantic = float(np.clip(self.provider.similarity(ea, eb), 0, 1))

        dims = DimensionScores(
            color=color_sim,
            symbols=symbols,
            semantic=semantic,
            archetypes=archetypes,
            emotions=emotions,
            elements=elements,
            numerology=numerology,
            narrative=narrative,
        )
        contrib = DimensionScores(
            **{k: getattr(dims, k) * weights[k] for k in weights}
        )
        total = sum(getattr(contrib, k) for k in weights)

        shared_kw = sorted(
            set(a.palabras_clave.neutrales + a.palabras_clave.luz + a.palabras_clave.sombra)
            & set(b.palabras_clave.neutrales + b.palabras_clave.luz + b.palabras_clave.sombra)
        )
        diffs: list[str] = []
        only_a = set(a.simbolos) - set(b.simbolos)
        only_b = set(b.simbolos) - set(a.simbolos)
        if only_a:
            diffs.append(f"Símbolos solo en {a.nombre}: {', '.join(sorted(only_a)[:5])}")
        if only_b:
            diffs.append(f"Símbolos solo en {b.nombre}: {', '.join(sorted(only_b)[:5])}")
        if a.elementos != b.elementos:
            diffs.append(f"Elementos: {a.elementos} vs {b.elementos}")
        if a.colores.temperatura_visual != b.colores.temperatura_visual:
            diffs.append(
                f"Temperatura visual: {a.colores.temperatura_visual} vs {b.colores.temperatura_visual}"
            )

        active = [k for k, w in weights.items() if w > 0 and getattr(dims, k) >= 0.4]

        explanation = SimilarityExplanation(
            shared_symbols=sorted(set(a.simbolos) & set(b.simbolos)),
            shared_archetypes=sorted(set(a.arquetipos) & set(b.arquetipos)),
            shared_emotions=sorted(set(a.emociones) & set(b.emociones)),
            related_keywords=shared_kw[:12],
            shared_elements=sorted(set(a.elementos) & set(b.elementos)),
            color_notes=color_notes[:6],
            main_differences=diffs[:8],
            active_dimensions=active,
        )

        return SimilarityResult(
            card_a=a.id,
            card_b=b.id,
            similarity_total=float(total),
            dimensions=dims,
            contributions=contrib,
            explanation=explanation,
            profile=profile_name,
            model_version=self.model_version,
        )
