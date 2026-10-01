"""Utilidades compartidas: rutas, config, logging, hashes."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def get_root() -> Path:
    return ROOT


def load_yaml(path: Path | str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML raíz debe ser mapping: {path}")
    return data


def load_pipeline_config() -> dict[str, Any]:
    return load_yaml(ROOT / "config" / "pipeline.yaml")


def load_similarity_config() -> dict[str, Any]:
    return load_yaml(ROOT / "config" / "similarity_weights.yaml")


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def env_path(key: str, default: Path) -> Path:
    value = os.getenv(key)
    return Path(value) if value else default
