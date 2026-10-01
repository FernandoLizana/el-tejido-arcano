"""Cerebro 3D esquemático (landmarks) + cartas del tarot — Plotly."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core.neuro_map import load_card_links, load_regions
from schemas.card_schema import CardDNA


def _ellipsoid_cloud(n: int = 900, seed: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    # Unit sphere then stretch to brain-ish oval
    vec = rng.normal(size=(n, 3))
    vec /= np.linalg.norm(vec, axis=1, keepdims=True)
    # hemisphere bias slightly
    scales = np.array([1.05, 1.35, 0.85])
    pts = vec * scales
    # keep cortical shell
    r = 0.82 + 0.18 * rng.random(n)
    pts = pts * r[:, None]
    return pts[:, 0], pts[:, 1], pts[:, 2]


def _card_orbit(region_xyz: tuple[float, float, float], k: int, i: int) -> tuple[float, float, float]:
    angle = (2 * np.pi * i) / max(k, 1) + 0.4
    ox, oy, oz = region_xyz
    return (
        float(ox + 0.28 * np.cos(angle)),
        float(oy + 0.22 * np.sin(angle)),
        float(oz + 0.18 * np.sin(angle * 1.3)),
    )


def build_brain_figure(
    cards: list[CardDNA],
    highlight_region: str | None = None,
    highlight_card: str | None = None,
    title: str = "Constelación cerebral · El Tejido Arcano",
) -> go.Figure:
    regions = load_regions()
    links = load_card_links()
    by_id = {c.id: c for c in cards}

    fig = go.Figure()
    bx, by, bz = _ellipsoid_cloud()
    fig.add_trace(
        go.Scatter3d(
            x=bx,
            y=by,
            z=bz,
            mode="markers",
            marker=dict(size=2, color="rgba(180,170,160,0.18)", opacity=0.55),
            name="Corteza (esquema)",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    # Midline guide
    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[-1.4, 1.45],
            z=[0, 0],
            mode="lines",
            line=dict(color="rgba(212,175,106,0.25)", width=2),
            name="Eje",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    rx, ry, rz, rtext, rcolors, rsizes = [], [], [], [], [], []
    for rid, reg in regions.items():
        x, y, z = reg.xyz
        glow = highlight_region == rid or (
            highlight_card
            and links.get(highlight_card)
            and (
                links[highlight_card].primary == rid
                or rid in links[highlight_card].secondary
            )
        )
        rx.append(x)
        ry.append(y)
        rz.append(z)
        rtext.append(
            f"<b>{reg.nombre}</b><br>{reg.sistema}<br><br>{reg.hecho_breve}"
        )
        rcolors.append(reg.color if glow or not highlight_region else "rgba(120,110,100,0.35)")
        rsizes.append(16 if glow else 11)

    fig.add_trace(
        go.Scatter3d(
            x=rx,
            y=ry,
            z=rz,
            mode="markers+text",
            text=[regions[rid].nombre.split("(")[0].strip()[:18] for rid in regions],
            textposition="top center",
            textfont=dict(size=10, color="#e8d2a0"),
            marker=dict(size=rsizes, color=rcolors, line=dict(width=1, color="#1a1620"), opacity=0.95),
            hovertext=rtext,
            hoverinfo="text",
            name="Regiones",
            customdata=list(regions.keys()),
        )
    )

    # Cards as satellites + edges to primary region
    cx, cy, cz, ctext, ccolors, csizes = [], [], [], [], [], []
    ex, ey, ez = [], [], []

    # group cards by primary for orbit index
    by_primary: dict[str, list[str]] = {}
    for cid, L in links.items():
        by_primary.setdefault(L.primary, []).append(cid)

    for rid, cids in by_primary.items():
        reg = regions[rid]
        for i, cid in enumerate(cids):
            card = by_id.get(cid)
            if not card:
                continue
            x, y, z = _card_orbit(reg.xyz, len(cids), i)
            focus = highlight_card == cid or (
                highlight_region and (links[cid].primary == highlight_region or highlight_region in links[cid].secondary)
            )
            dim = bool(highlight_region or highlight_card) and not focus
            cx.append(x)
            cy.append(y)
            cz.append(z)
            jodo = ""
            for s in card.significados:
                if "Jodorowsky" in " ".join(s.autores):
                    jodo = (s.subtitulo or "")[:120]
                    break
            ctext.append(
                f"<b>{card.nombre}</b><br>→ {reg.nombre}<br>{links[cid].rationale}<br><i>{jodo}</i>"
            )
            ccolors.append("#f3ebe0" if focus or not dim else "rgba(130,120,110,0.35)")
            csizes.append(9 if focus else 6)
            # edge
            ex += [reg.xyz[0], x, None]
            ey += [reg.xyz[1], y, None]
            ez += [reg.xyz[2], z, None]

    fig.add_trace(
        go.Scatter3d(
            x=ex,
            y=ey,
            z=ez,
            mode="lines",
            line=dict(color="rgba(212,175,106,0.35)", width=2),
            name="Vínculos",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=cx,
            y=cy,
            z=cz,
            mode="markers",
            marker=dict(size=csizes, color=ccolors, symbol="diamond", line=dict(width=0.5, color="#d4af6a")),
            hovertext=ctext,
            hoverinfo="text",
            name="Arcanos",
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#e8d2a0", size=16, family="Fraunces, serif")),
        paper_bgcolor="#100e14",
        scene=dict(
            bgcolor="#121018",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="data",
            camera=dict(eye=dict(x=1.55, y=1.25, z=0.85)),
        ),
        margin=dict(l=0, r=0, t=48, b=0),
        legend=dict(font=dict(color="#c9c0b4", size=11), bgcolor="rgba(0,0,0,0)"),
        height=620,
    )
    return fig


def region_choices() -> list[tuple[str, str]]:
    return [(r.nombre, r.id) for r in load_regions().values()]
