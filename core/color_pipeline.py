"""Pipeline cromático reproducible: RGB → LAB, ΔE, histograma, temperatura."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


@dataclass
class ColorExtractionResult:
    rgb: list[list[int]]
    hex: list[str]
    lab: list[list[float]]
    percentages: list[float]
    luminosidad_media: float
    saturacion_media: float
    temperatura_visual: str
    histograma_hue_bins: list[float]


def rgb_to_hex(rgb: tuple[int, ...] | list[int]) -> str:
    r, g, b = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rgb_to_xyz(rgb: np.ndarray) -> np.ndarray:
    """rgb shape (..., 3) uint/float 0-255 → XYZ D65."""
    linear = _srgb_to_linear(rgb.astype(np.float64))
    m = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    return linear @ m.T


def xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    """XYZ → CIELAB D65."""
    ref = np.array([0.95047, 1.0, 1.08883])
    x = xyz / ref

    def f(t: np.ndarray) -> np.ndarray:
        delta = 6 / 29
        return np.where(t > delta**3, np.cbrt(t), t / (3 * delta**2) + 4 / 29)

    fx, fy, fz = f(x[..., 0]), f(x[..., 1]), f(x[..., 2])
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    return xyz_to_lab(rgb_to_xyz(rgb))


def delta_e76(lab1: np.ndarray, lab2: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(lab1, dtype=float) - np.asarray(lab2, dtype=float)))


def delta_e2000(lab1: np.ndarray, lab2: np.ndarray) -> float:
    """CIEDE2000 (implementación compacta)."""
    L1, a1, b1 = [float(x) for x in lab1]
    L2, a2, b2 = [float(x) for x in lab2]
    kL = kC = kH = 1.0

    C1 = np.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    Cab = (C1 + C2) / 2.0
    G = 0.5 * (1 - np.sqrt(Cab**7 / (Cab**7 + 25**7))) if Cab else 0.0
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360

    dLp = L2 - L1
    dCp = C2p - C1p
    dhp = h2p - h1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif dhp > 180:
        dhp -= 360
    elif dhp < -180:
        dhp += 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp) / 2.0)

    Lp = (L1 + L2) / 2.0
    Cp = (C1p + C2p) / 2.0
    hp = (h1p + h2p) / 2.0
    if C1p * C2p != 0 and abs(h1p - h2p) > 180:
        hp += 180 if (h1p + h2p) < 360 else -180

    T = (
        1
        - 0.17 * np.cos(np.radians(hp - 30))
        + 0.24 * np.cos(np.radians(2 * hp))
        + 0.32 * np.cos(np.radians(3 * hp + 6))
        - 0.20 * np.cos(np.radians(4 * hp - 63))
    )
    dRo = 30 * np.exp(-(((hp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cp**7 / (Cp**7 + 25**7)) if Cp else 0.0
    Sl = 1 + (0.015 * (Lp - 50) ** 2) / np.sqrt(20 + (Lp - 50) ** 2)
    Sc = 1 + 0.045 * Cp
    Sh = 1 + 0.015 * Cp * T
    Rt = -np.sin(np.radians(2 * dRo)) * Rc

    return float(
        np.sqrt(
            (dLp / (kL * Sl)) ** 2
            + (dCp / (kC * Sc)) ** 2
            + (dHp / (kH * Sh)) ** 2
            + Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh))
        )
    )


def _rgb_to_hsv_batch(rgb: np.ndarray) -> np.ndarray:
    arr = rgb.astype(np.float64) / 255.0
    r, g, b = arr[:, 0], arr[:, 1], arr[:, 2]
    mx = np.max(arr, axis=1)
    mn = np.min(arr, axis=1)
    df = mx - mn
    h = np.zeros_like(mx)
    mask = df != 0
    idx = (mx == r) & mask
    h[idx] = (60 * ((g[idx] - b[idx]) / df[idx]) + 360) % 360
    idx = (mx == g) & mask
    h[idx] = (60 * ((b[idx] - r[idx]) / df[idx]) + 120) % 360
    idx = (mx == b) & mask
    h[idx] = (60 * ((r[idx] - g[idx]) / df[idx]) + 240) % 360
    s = np.where(mx == 0, 0, df / np.maximum(mx, 1e-12))
    v = mx
    return np.stack([h, s, v], axis=1)


def classify_temperature(rgb_colors: list[list[int]], weights: list[float]) -> str:
    if not rgb_colors:
        return "desconocida"
    warm = cold = 0.0
    for c, w in zip(rgb_colors, weights):
        r, g, b = c
        if r > b + 15:
            warm += w
        elif b > r + 15:
            cold += w
    if warm - cold > 0.12:
        return "calida"
    if cold - warm > 0.12:
        return "fria"
    return "neutra"


def extract_colors(
    image_path: str | Path,
    k: int = 5,
    seed: int = 42,
    resize: int = 120,
    border_crop_ratio: float = 0.06,
    exclude_near_white: bool = True,
    near_white_threshold: int = 245,
    exclude_near_black: bool = False,
    near_black_threshold: int = 12,
) -> ColorExtractionResult:
    """Extrae paleta dominante ordenada por proporción de píxeles."""
    path = Path(image_path)
    imagen = Image.open(path).convert("RGB")
    w, h = imagen.size
    crop = int(min(w, h) * border_crop_ratio)
    if crop > 0:
        imagen = imagen.crop((crop, crop, w - crop, h - crop))
    imagen = imagen.resize((resize, resize), Image.Resampling.LANCZOS)
    pixels = np.array(imagen).reshape(-1, 3)

    mask = np.ones(len(pixels), dtype=bool)
    if exclude_near_white:
        mask &= pixels.min(axis=1) < near_white_threshold
    if exclude_near_black:
        mask &= pixels.max(axis=1) > near_black_threshold
    filtered = pixels[mask]
    if len(filtered) < k * 10:
        filtered = pixels
        logger.warning("Pocos píxeles tras filtro en %s; se usan todos", path.name)

    k_eff = max(1, min(k, len(np.unique(filtered, axis=0))))
    km = KMeans(n_clusters=k_eff, random_state=seed, n_init=10)
    labels = km.fit_predict(filtered)
    centers = km.cluster_centers_
    counts = np.bincount(labels, minlength=k_eff).astype(float)
    order = np.argsort(-counts)
    centers = centers[order]
    counts = counts[order]
    percentages = (counts / counts.sum()).tolist()

    rgb = [[int(round(c[0])), int(round(c[1])), int(round(c[2]))] for c in centers]
    lab = rgb_to_lab(np.array(rgb, dtype=float)).tolist()
    hexes = [rgb_to_hex(c) for c in rgb]

    hsv_all = _rgb_to_hsv_batch(filtered)
    luminosidad = float(hsv_all[:, 2].mean())
    saturacion = float(hsv_all[:, 1].mean())
    hist, _ = np.histogram(hsv_all[:, 0], bins=12, range=(0, 360), density=True)
    hist = (hist / max(hist.sum(), 1e-12)).tolist()
    temp = classify_temperature(rgb, percentages)

    return ColorExtractionResult(
        rgb=rgb,
        hex=hexes,
        lab=[[float(x) for x in row] for row in lab],
        percentages=percentages,
        luminosidad_media=luminosidad,
        saturacion_media=saturacion,
        temperatura_visual=temp,
        histograma_hue_bins=hist,
    )


def palette_similarity(
    lab_a: list[list[float]],
    pct_a: list[float],
    lab_b: list[list[float]],
    pct_b: list[float],
    max_delta: float = 50.0,
) -> tuple[float, list[str]]:
    """
    Similitud [0,1] por emparejamiento ponderado con ΔE2000.
    Aproxima transporte: cada color de A se empareja al más cercano de B.
    """
    if not lab_a or not lab_b:
        return 0.0, ["Sin paleta en una o ambas cartas"]

    notes: list[str] = []
    score_ab = 0.0
    for i, (la, pa) in enumerate(zip(lab_a, pct_a)):
        dists = [delta_e2000(la, lb) for lb in lab_b]
        j = int(np.argmin(dists))
        d = dists[j]
        sim = max(0.0, 1.0 - d / max_delta)
        score_ab += pa * sim
        if d < 15:
            notes.append(f"Color A#{i+1} cercano a B#{j+1} (ΔE={d:.1f})")

    score_ba = 0.0
    for i, (lb, pb) in enumerate(zip(lab_b, pct_b)):
        dists = [delta_e2000(lb, la) for la in lab_a]
        j = int(np.argmin(dists))
        d = dists[j]
        sim = max(0.0, 1.0 - d / max_delta)
        score_ba += pb * sim

    total = 0.5 * (score_ab + score_ba)
    return float(np.clip(total, 0, 1)), notes


def color_features_to_dict(result: ColorExtractionResult) -> dict[str, Any]:
    return {
        "dominantes_rgb": result.rgb,
        "dominantes_hex": result.hex,
        "dominantes_lab": result.lab,
        "porcentajes": result.percentages,
        "luminosidad_media": result.luminosidad_media,
        "saturacion_media": result.saturacion_media,
        "temperatura_visual": result.temperatura_visual,
        "histograma_hue_bins": result.histograma_hue_bins,
    }
