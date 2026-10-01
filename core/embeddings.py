"""Proveedores de embeddings locales / TF-IDF / API opcional."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.utils import ensure_dir, stable_hash

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    name: str

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        ...

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if a.ndim == 1:
            a = a.reshape(1, -1)
        if b.ndim == 1:
            b = b.reshape(1, -1)
        return float(cosine_similarity(a, b)[0, 0])


class TfidfProvider(EmbeddingProvider):
    name = "tfidf"

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self._fitted = False
        self._matrix: np.ndarray | None = None
        self._texts: list[str] = []

    def fit(self, texts: Sequence[str]) -> None:
        self._texts = list(texts)
        self._matrix = self._vectorizer.fit_transform(self._texts)
        self._fitted = True

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not self._fitted:
            self.fit(texts)
            return self._matrix.toarray()  # type: ignore[union-attr]
        return self._vectorizer.transform(list(texts)).toarray()


class LocalEmbeddingProvider(EmbeddingProvider):
    """Intenta sentence-transformers; si falta, cae a TF-IDF."""

    name = "local"

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._fallback = TfidfProvider()
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(model_name)
            logger.info("LocalEmbeddingProvider cargado: %s", model_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("sentence-transformers no disponible (%s); fallback TF-IDF", exc)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if self._model is None:
            return self._fallback.embed(texts)
        return np.asarray(self._model.encode(list(texts), normalize_embeddings=True))


class OptionalApiEmbeddingProvider(EmbeddingProvider):
    name = "api"

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.url = url
        self.api_key = api_key
        self._fallback = TfidfProvider()
        if not url:
            logger.info("OptionalApiEmbeddingProvider sin URL; usa TF-IDF")

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not self.url or not self.api_key:
            return self._fallback.embed(texts)
        try:
            import httpx

            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = httpx.post(self.url, json={"texts": list(texts)}, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()["embeddings"]
            return np.asarray(data, dtype=float)
        except Exception as exc:  # noqa: BLE001
            logger.warning("API embeddings falló (%s); fallback TF-IDF", exc)
            return self._fallback.embed(texts)


def get_provider(name: str = "tfidf") -> EmbeddingProvider:
    name = (name or "tfidf").lower()
    if name == "local":
        return LocalEmbeddingProvider()
    if name == "api":
        import os

        return OptionalApiEmbeddingProvider(
            url=os.getenv("ARCANAGRAPH_API_EMBEDDING_URL"),
            api_key=os.getenv("ARCANAGRAPH_API_EMBEDDING_KEY"),
        )
    return TfidfProvider()


class EmbeddingCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = ensure_dir(cache_dir)

    def _path(self, card_id: str, content_hash: str, provider: str) -> Path:
        return self.cache_dir / f"{card_id}__{provider}__{content_hash[:16]}.json"

    def load(self, card_id: str, content_hash: str, provider: str) -> np.ndarray | None:
        path = self._path(card_id, content_hash, provider)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return np.asarray(data["vector"], dtype=float)

    def save(self, card_id: str, content_hash: str, provider: str, vector: np.ndarray) -> None:
        path = self._path(card_id, content_hash, provider)
        payload = {
            "card_id": card_id,
            "content_hash": content_hash,
            "provider": provider,
            "vector": vector.tolist(),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
