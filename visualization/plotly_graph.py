"""Visualización Plotly 2D/3D con atmósfera y animación."""

from __future__ import annotations

from typing import Any, Literal

import networkx as nx
import numpy as np
import plotly.graph_objects as go

from core.metrics import detect_communities, graph_metrics


def _palette() -> list[str]:
    return [
        "#d4af6a",
        "#6a9e98",
        "#c47a5a",
        "#8eb3c9",
        "#b08968",
        "#9bc4b0",
        "#e0c07a",
        "#7f8fab",
        "#c9a08a",
        "#a8b5a2",
    ]


def build_figure(
    G: nx.Graph,
    dim: Literal[2, 3] = 3,
    color_by: Literal["community", "element", "dominant"] = "community",
    show_labels: bool = False,
    title: str = "El Tejido Arcano",
    preset: str = "constelacion",
    animate: bool = True,
) -> go.Figure:
    metrics = graph_metrics(G)
    communities = metrics.get("communities") or detect_communities(G)
    comm_index = {n: i for i, community in enumerate(communities) for n in community}

    pos = nx.spring_layout(G, dim=dim, seed=42, weight="weight", iterations=55)
    central = metrics.get("betweenness") or {n: 0.12 for n in G.nodes()}
    max_c = max(central.values()) if central else 1.0
    palette = _palette()
    nodes = list(G.nodes())

    base = []
    for n in nodes:
        p = pos[n]
        if dim == 2:
            base.append([p[0], p[1], 0.0])
        else:
            base.append([p[0], p[1], p[2]])
    base_xyz = np.asarray(base, dtype=float)

    # Un solo trazo de aristas (más fluido al animar)
    ex, ey, ez = [], [], []
    for u, v, d in G.edges(data=True):
        p0, p1 = pos[u], pos[v]
        ex += [p0[0], p1[0], None]
        ey += [p0[1], p1[1], None]
        if dim == 3:
            ez += [p0[2], p1[2], None]
        else:
            ez += [0, 0, None]

    if dim == 3:
        edge_trace = go.Scatter3d(
            x=ex,
            y=ey,
            z=ez,
            mode="lines",
            line=dict(color="rgba(212,175,106,0.38)", width=2),
            hoverinfo="none",
            showlegend=False,
        )
    else:
        edge_trace = go.Scatter(
            x=ex,
            y=ey,
            mode="lines",
            line=dict(color="rgba(212,175,106,0.4)", width=1.4),
            hoverinfo="none",
            showlegend=False,
        )

    colors, sizes, texts, labels = [], [], [], []
    for n in nodes:
        sizes.append(11 + 20 * (central.get(n, 0) / max_c if max_c else 0))
        if color_by == "community":
            colors.append(palette[comm_index.get(n, 0) % len(palette)])
        elif color_by == "dominant":
            colors.append(G.nodes[n].get("color_hex", "#d4af6a"))
        else:
            els = tuple(G.nodes[n].get("elementos") or [])
            colors.append(palette[hash(els) % len(palette)])
        name = G.nodes[n].get("nombre", n)
        texts.append(f"<b>{name}</b><br>conexiones: {G.degree(n)}")
        labels.append(name if show_labels else "")

    def make_nodes(scale: float, xyz: np.ndarray) -> Any:
        marker = dict(
            size=[float(s * scale) for s in sizes],
            color=colors,
            opacity=0.93,
            line=dict(width=1, color="rgba(12,10,16,0.9)"),
        )
        if dim == 3:
            return go.Scatter3d(
                x=xyz[:, 0],
                y=xyz[:, 1],
                z=xyz[:, 2],
                mode="markers+text" if show_labels else "markers",
                text=labels,
                hovertext=texts,
                hoverinfo="text",
                marker=marker,
                textposition="top center",
                textfont=dict(size=11, color="#f3ebe0", family="Sora, sans-serif"),
            )
        return go.Scatter(
            x=xyz[:, 0],
            y=xyz[:, 1],
            mode="markers+text" if show_labels else "markers",
            text=labels,
            hovertext=texts,
            hoverinfo="text",
            marker=marker,
            textposition="top center",
            textfont=dict(size=11, color="#f3ebe0", family="Sora, sans-serif"),
        )

    fig = go.Figure(data=[edge_trace, make_nodes(1.0, base_xyz)])

    layout: dict[str, Any] = dict(
        title=dict(text=title, font=dict(family="Fraunces, serif", size=20, color="#f3ebe0")),
        showlegend=False,
        paper_bgcolor="rgba(12,10,16,0)",
        plot_bgcolor="rgba(12,10,16,0)",
        margin=dict(l=0, r=0, b=48, t=52),
        font=dict(family="Sora, sans-serif", color="#c9c0b4"),
        annotations=[
            dict(
                text="Experimental · pulsa ▷ Animar · gira con el mouse",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=1,
                y=0,
                xanchor="right",
                font=dict(size=11, color="#8a8278"),
            )
        ],
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=0.02,
                x=0.02,
                xanchor="left",
                yanchor="bottom",
                bgcolor="rgba(34,28,40,0.9)",
                bordercolor="rgba(212,175,106,0.35)",
                font=dict(color="#e8d2a0"),
                buttons=[
                    dict(
                        label="▷ Animar",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=60, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="❚❚ Pausa",
                        method="animate",
                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                    ),
                ],
            )
        ],
    )

    if dim == 3:
        layout["scene"] = dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.5, y=1.1, z=0.9)),
        )
    else:
        layout["xaxis"] = dict(visible=False)
        layout["yaxis"] = dict(visible=False)

    fig.update_layout(**layout)

    if animate and nodes:
        frames = []
        n_frames = 40
        for i in range(n_frames):
            t = i / n_frames
            scale = 1.0 + 0.14 * np.sin(2 * np.pi * t)
            breath = 1.0 + 0.028 * np.sin(2 * np.pi * t)
            xyz = base_xyz * breath
            # edges also breathe slightly
            if dim == 3:
                ex2, ey2, ez2 = [], [], []
                for u, v in G.edges():
                    a = pos[u]
                    b = pos[v]
                    ex2 += [a[0] * breath, b[0] * breath, None]
                    ey2 += [a[1] * breath, b[1] * breath, None]
                    ez2 += [a[2] * breath, b[2] * breath, None]
                edge_f = go.Scatter3d(
                    x=ex2,
                    y=ey2,
                    z=ez2,
                    mode="lines",
                    line=dict(color="rgba(212,175,106,0.38)", width=2),
                    hoverinfo="none",
                    showlegend=False,
                )
            else:
                ex2, ey2 = [], []
                for u, v in G.edges():
                    a = pos[u]
                    b = pos[v]
                    ex2 += [a[0] * breath, b[0] * breath, None]
                    ey2 += [a[1] * breath, b[1] * breath, None]
                edge_f = go.Scatter(
                    x=ex2,
                    y=ey2,
                    mode="lines",
                    line=dict(color="rgba(212,175,106,0.4)", width=1.4),
                    hoverinfo="none",
                    showlegend=False,
                )

            ang = 2 * np.pi * t
            if dim == 3:
                frames.append(
                    go.Frame(
                        data=[edge_f, make_nodes(float(scale), xyz)],
                        name=f"f{i}",
                        layout=dict(
                            scene_camera=dict(
                                eye=dict(
                                    x=1.55 * np.cos(ang),
                                    y=1.55 * np.sin(ang),
                                    z=0.78 + 0.22 * np.sin(ang * 0.5),
                                )
                            )
                        ),
                    )
                )
            else:
                frames.append(go.Frame(data=[edge_f, make_nodes(float(scale), xyz)], name=f"f{i}"))
        fig.frames = frames

    return fig
