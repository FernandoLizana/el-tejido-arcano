"""ML local: visión, texto y estructura de grafo (explicable, con fallbacks)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from core.card_repository import load_all_cards
from core.embeddings import EmbeddingCache, get_provider
from core.similarity_engine import SimilarityEngine, card_semantic_text
from core.utils import ensure_dir, get_root, load_pipeline_config, stable_hash
from schemas.card_schema import CardDNA

logger = logging.getLogger(__name__)

Mode = Literal["vision", "texto", "grafo", "combinado"]


@dataclass
class Recommendation:
    card_id: str
    score: float
    mode: str
    reasons: list[str]


def _image_path(card: CardDNA) -> Path | None:
    root = get_root()
    candidates = [
        root / card.imagen,
        root / "cartas" / Path(card.imagen).name,
        root / "assets" / "cards" / "rws" / Path(card.imagen).name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def extract_vision_vector(
    image_path: Path,
    size: int = 64,
    hue_bins: int = 12,
    edge_bins: int = 8,
) -> np.ndarray:
    """
    Embedding visual local (sin GPU):
    histograma HSV + estadísticas LAB aproximadas + energía de bordes.
    """
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    crop = int(min(w, h) * 0.06)
    if crop > 0:
        img = img.crop((crop, crop, w - crop, h - crop))
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.float64)

    # HSV hist
    rgb = arr.reshape(-1, 3) / 255.0
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    df = mx - mn
    h_ch = np.zeros_like(mx)
    mask = df > 1e-9
    idx = (mx == r) & mask
    h_ch[idx] = ((g[idx] - b[idx]) / df[idx]) % 6
    idx = (mx == g) & mask
    h_ch[idx] = (b[idx] - r[idx]) / df[idx] + 2
    idx = (mx == b) & mask
    h_ch[idx] = (r[idx] - g[idx]) / df[idx] + 4
    hue = (h_ch / 6.0) * 360.0
    sat = np.where(mx == 0, 0, df / np.maximum(mx, 1e-9))
    val = mx
    h_hist, _ = np.histogram(hue, bins=hue_bins, range=(0, 360), density=True)
    s_hist, _ = np.histogram(sat, bins=8, range=(0, 1), density=True)
    v_hist, _ = np.histogram(val, bins=8, range=(0, 1), density=True)

    # Channel means / std
    stats = np.array(
        [
            arr[:, :, 0].mean(),
            arr[:, :, 1].mean(),
            arr[:, :, 2].mean(),
            arr[:, :, 0].std(),
            arr[:, :, 1].std(),
            arr[:, :, 2].std(),
        ]
    )

    # Simple edge energy (gradient magnitude)
    gray = arr.mean(axis=2)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    # pad to same shape roughly
    edge = np.concatenate([gx.ravel(), gy.ravel()])
    e_hist, _ = np.histogram(edge, bins=edge_bins, range=(0, 255), density=True)

    # Compact spatial grid (4x4 mean color)
    grid = []
    step = size // 4
    for i in range(4):
        for j in range(4):
            block = arr[i * step : (i + 1) * step, j * step : (j + 1) * step]
            grid.extend(block.mean(axis=(0, 1)).tolist())

    vec = np.concatenate([h_hist, s_hist, v_hist, stats / 255.0, e_hist, np.array(grid) / 255.0])
    return vec.astype(np.float64)


class VisionIndex:
    def __init__(self, cache_dir: Path | None = None, pca_dim: int = 24, seed: int = 42) -> None:
        self.cache_dir = ensure_dir(cache_dir or get_root() / "data" / "cache" / "vision")
        self.pca_dim = pca_dim
        self.seed = seed
        self.card_ids: list[str] = []
        self.matrix: np.ndarray | None = None
        self._raw: dict[str, np.ndarray] = {}

    def _cache_path(self, card_id: str, content_hash: str) -> Path:
        return self.cache_dir / f"{card_id}__{content_hash[:16]}.npy"

    def fit(self, cards: list[CardDNA]) -> None:
        vectors = []
        ids = []
        for card in cards:
            path = _image_path(card)
            if path is None:
                logger.warning("Sin imagen para visión: %s", card.id)
                continue
            ch = stable_hash({"id": card.id, "img": str(path), "mtime": path.stat().st_mtime})
            cpath = self._cache_path(card.id, ch)
            if cpath.exists():
                vec = np.load(cpath)
            else:
                vec = extract_vision_vector(path)
                np.save(cpath, vec)
            self._raw[card.id] = vec
            vectors.append(vec)
            ids.append(card.id)

        if not vectors:
            self.card_ids = []
            self.matrix = None
            return

        X = np.vstack(vectors)
        n_comp = min(self.pca_dim, X.shape[0], X.shape[1])
        if n_comp >= 2:
            pca = PCA(n_components=n_comp, random_state=self.seed)
            X = pca.fit_transform(X)
        X = normalize(X)
        self.card_ids = ids
        self.matrix = X
        logger.info("VisionIndex listo: %s cartas, dim=%s", len(ids), X.shape[1])

    def similarity_matrix(self) -> dict[tuple[str, str], float]:
        out: dict[tuple[str, str], float] = {}
        if self.matrix is None:
            return out
        sims = cosine_similarity(self.matrix)
        for i, a in enumerate(self.card_ids):
            for j in range(i + 1, len(self.card_ids)):
                b = self.card_ids[j]
                out[tuple(sorted((a, b)))] = float(sims[i, j])
        return out

    def neighbors(self, card_id: str, k: int = 5) -> list[tuple[str, float]]:
        if self.matrix is None or card_id not in self.card_ids:
            return []
        i = self.card_ids.index(card_id)
        sims = cosine_similarity(self.matrix[i : i + 1], self.matrix)[0]
        order = np.argsort(-sims)
        res = []
        for idx in order:
            cid = self.card_ids[idx]
            if cid == card_id:
                continue
            res.append((cid, float(sims[idx])))
            if len(res) >= k:
                break
        return res


class TextIndex:
    def __init__(self, provider_name: str | None = None) -> None:
        pipe = load_pipeline_config()
        self.provider = get_provider(provider_name or pipe.get("embedding_provider", "tfidf"))
        self.cache = EmbeddingCache(get_root() / "data" / "cache" / "embeddings")
        self.card_ids: list[str] = []
        self.matrix: np.ndarray | None = None
        self.provider_status = getattr(self.provider, "name", "unknown")

    def fit(self, cards: list[CardDNA]) -> None:
        texts = [card_semantic_text(c) for c in cards]
        # fit corpus once for tfidf
        vectors = self.provider.embed(texts)
        mats = []
        ids = []
        for card, vec in zip(cards, vectors):
            ch = stable_hash(card.content_hash_payload())
            cached = self.cache.load(card.id, ch, self.provider.name)
            if cached is not None:
                v = cached
            else:
                v = np.asarray(vec, dtype=float)
                self.cache.save(card.id, ch, self.provider.name, v)
            mats.append(v)
            ids.append(card.id)
        X = np.vstack(mats)
        # Pad / truncate to same dim if needed
        X = normalize(X)
        self.card_ids = ids
        self.matrix = X
        logger.info("TextIndex (%s) listo: %s cartas", self.provider_status, len(ids))

    def neighbors(self, card_id: str, k: int = 5) -> list[tuple[str, float]]:
        if self.matrix is None or card_id not in self.card_ids:
            return []
        i = self.card_ids.index(card_id)
        sims = cosine_similarity(self.matrix[i : i + 1], self.matrix)[0]
        order = np.argsort(-sims)
        res = []
        for idx in order:
            cid = self.card_ids[idx]
            if cid == card_id:
                continue
            res.append((cid, float(max(0.0, sims[idx]))))
            if len(res) >= k:
                break
        return res

    def search_query(self, query: str, cards: list[CardDNA], k: int = 8) -> list[tuple[str, float]]:
        if self.matrix is None:
            self.fit(cards)
        assert self.matrix is not None
        q = self.provider.embed([query])[0].reshape(1, -1)
        # align dims
        if q.shape[1] != self.matrix.shape[1]:
            # refetch by refitting is safer for tfidf
            self.fit(cards)
            q = self.provider.embed([query])[0].reshape(1, -1)
        sims = cosine_similarity(q, self.matrix)[0]
        order = np.argsort(-sims)
        return [(self.card_ids[i], float(max(0.0, sims[i]))) for i in order[:k]]


class GraphEmbeddingIndex:
    """Embeddings de nodos a partir de la matriz de similitud multidimensional."""

    def __init__(self, n_components: int = 8, seed: int = 42) -> None:
        self.n_components = n_components
        self.seed = seed
        self.card_ids: list[str] = []
        self.matrix: np.ndarray | None = None
        self.affinity: np.ndarray | None = None
        self.engine: SimilarityEngine | None = None

    def fit(self, cards: list[CardDNA], profile: str | None = None) -> None:
        engine = SimilarityEngine(profile=profile)
        engine.fit_corpus(cards)
        self.engine = engine
        n = len(cards)
        self.card_ids = [c.id for c in cards]
        A = np.zeros((n, n), dtype=float)
        for i in range(n):
            A[i, i] = 1.0
            for j in range(i + 1, n):
                res = engine.compare(cards[i], cards[j], profile=profile)
                A[i, j] = A[j, i] = res.similarity_total
        self.affinity = A
        # Spectral-ish: eigenvectors of normalized affinity
        # Use sklearn kernel PCA on precomputed affinity
        from sklearn.decomposition import KernelPCA

        n_comp = min(self.n_components, max(2, n - 1))
        kpca = KernelPCA(n_components=n_comp, kernel="precomputed", random_state=self.seed)
        X = kpca.fit_transform(A)
        self.matrix = normalize(X)
        logger.info("GraphEmbeddingIndex listo: %s nodos", n)

    def neighbors(self, card_id: str, k: int = 5) -> list[tuple[str, float]]:
        if self.matrix is None or card_id not in self.card_ids:
            return []
        i = self.card_ids.index(card_id)
        sims = cosine_similarity(self.matrix[i : i + 1], self.matrix)[0]
        order = np.argsort(-sims)
        res = []
        for idx in order:
            cid = self.card_ids[idx]
            if cid == card_id:
                continue
            res.append((cid, float(max(0.0, sims[idx]))))
            if len(res) >= k:
                break
        return res

    def explain_pair(self, a: str, b: str, cards_by_id: dict[str, CardDNA]) -> dict[str, Any]:
        if not self.engine or a not in cards_by_id or b not in cards_by_id:
            return {}
        res = self.engine.compare(cards_by_id[a], cards_by_id[b])
        dims = res.dimensions.model_dump()
        top = sorted(dims.items(), key=lambda x: -x[1])[:3]
        return {
            "similarity_total": res.similarity_total,
            "top_dimensions": top,
            "explanation": res.explanation.model_dump(),
        }


class MultimodalLab:
    """Orquesta visión + texto + grafo."""

    def __init__(self) -> None:
        pipe = load_pipeline_config()
        ml = pipe.get("ml", {})
        self.vision = VisionIndex(pca_dim=int(ml.get("vision_pca_dim", 24)), seed=int(pipe.get("seed", 42)))
        self.text = TextIndex(provider_name=ml.get("text_provider") or pipe.get("embedding_provider"))
        self.graph = GraphEmbeddingIndex(
            n_components=int(ml.get("graph_embedding_dim", 8)),
            seed=int(pipe.get("seed", 42)),
        )
        self._fitted = False
        self.cards: list[CardDNA] = []
        self.by_id: dict[str, CardDNA] = {}

    def fit(self, cards: list[CardDNA] | None = None, profile: str | None = None) -> None:
        self.cards = cards or load_all_cards()
        self.by_id = {c.id: c for c in self.cards}
        self.vision.fit(self.cards)
        self.text.fit(self.cards)
        self.graph.fit(self.cards, profile=profile)
        self._fitted = True
        # persist summary
        out = ensure_dir(get_root() / "data" / "cache" / "ml")
        summary = {
            "n_cards": len(self.cards),
            "vision_cards": len(self.vision.card_ids),
            "text_provider": self.text.provider_status,
            "graph_dim": None if self.graph.matrix is None else int(self.graph.matrix.shape[1]),
        }
        (out / "last_fit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def recommend(
        self,
        card_id: str,
        mode: Mode = "combinado",
        k: int = 5,
    ) -> list[Recommendation]:
        if not self._fitted:
            self.fit()
        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = {}

        def add(pairs: list[tuple[str, float]], label: str, weight: float = 1.0) -> None:
            for cid, s in pairs:
                scores[cid] = scores.get(cid, 0.0) + weight * s
                reasons.setdefault(cid, []).append(f"{label}: {int(round(s * 100))}%")

        if mode in ("vision", "combinado"):
            add(self.vision.neighbors(card_id, k=max(k, 8)), "parecido visual", 1.0 if mode == "vision" else 0.35)
        if mode in ("texto", "combinado"):
            add(self.text.neighbors(card_id, k=max(k, 8)), "parecido de significado", 1.0 if mode == "texto" else 0.40)
        if mode in ("grafo", "combinado"):
            add(self.graph.neighbors(card_id, k=max(k, 8)), "cercanía en la red", 1.0 if mode == "grafo" else 0.25)

        ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
        # normalize display score roughly
        out = []
        for cid, sc in ranked:
            extra = []
            if mode in ("grafo", "combinado") and self.graph.engine:
                info = self.graph.explain_pair(card_id, cid, self.by_id)
                if info.get("top_dimensions"):
                    dims = ", ".join(f"{d}={int(v*100)}%" for d, v in info["top_dimensions"])
                    extra.append(f"dimensiones fuertes: {dims}")
            out.append(
                Recommendation(
                    card_id=cid,
                    score=float(sc if mode != "combinado" else min(1.0, sc)),
                    mode=mode,
                    reasons=reasons.get(cid, []) + extra,
                )
            )
        return out

    def search_meaning(self, query: str, k: int = 8) -> list[Recommendation]:
        if not self._fitted:
            self.fit()
        hits = self.text.search_query(query, self.cards, k=k)
        return [
            Recommendation(
                card_id=cid,
                score=score,
                mode="texto",
                reasons=[f"coincide con la idea “{query}” ({int(score*100)}%)"],
            )
            for cid, score in hits
        ]
