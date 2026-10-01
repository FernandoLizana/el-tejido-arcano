"""
El Tejido Arcano — interfaz sencilla y experiencias atractivas.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.card_repository import load_all_cards  # noqa: E402
from core.experience import (  # noqa: E402
    build_story,
    card_of_the_day,
    constellation_focus,
    export_lamina,
    make_bridge_challenge,
)
from core.games import (  # noqa: E402
    cinema_spread,
    make_memory_round,
    make_odd_one_out,
    minute_oracle,
)
from core.graph_builder import GraphBuilder  # noqa: E402
from core.metrics import graph_metrics  # noqa: E402
from core.ml_lab import MultimodalLab  # noqa: E402
from core.neuro_map import (  # noqa: E402
    explore_by_card,
    explore_by_region,
    load_regions,
    map_disclaimer,
)
from core.personality_quiz import (  # noqa: E402
    QUESTIONS,
    guide_card_from_birthdate,
    personal_spread_from_birthdate,
    score_quiz,
)
from core.similarity_engine import SimilarityEngine  # noqa: E402
from core.spread_analyzer import SpreadAnalyzer, find_hidden_path  # noqa: E402
from visualization.brain_3d import build_brain_figure  # noqa: E402
from visualization.plotly_graph import build_figure  # noqa: E402
from ui.theme import hero, inject_theme  # noqa: E402

st.set_page_config(
    page_title="El Tejido Arcano",
    page_icon="✧",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

MODOS = {
    "Ver todo junto (recomendado)": "equilibrado",
    "Por colores e imágenes": "visual",
    "Por emociones y psicología": "psicologico",
    "Por tradición simbólica": "tradicional",
    "Por historia / relato": "narrativo",
}

VISTAS = {
    "Todas las relaciones": "combined",
    "Solo colores": "color",
    "Solo símbolos": "symbols",
    "Solo significados": "semantic",
    "Solo arquetipos": "archetypes",
    "Solo emociones": "emotions",
    "Solo etapas de la historia": "narrative",
}

DIM_LABELS = {
    "color": "Colores de la carta",
    "symbols": "Símbolos dibujados",
    "semantic": "Significados / palabras",
    "archetypes": "Arquetipos",
    "emotions": "Emociones",
    "elements": "Elementos (fuego, agua…)",
    "numerology": "Números",
    "narrative": "Etapas de la historia",
}


@st.cache_resource
def get_builder() -> GraphBuilder:
    return GraphBuilder()


@st.cache_resource
def get_ml_lab() -> MultimodalLab:
    lab = MultimodalLab()
    lab.fit(load_all_cards())
    return lab


@st.cache_data(ttl=60)
def cards_list():
    return load_all_cards()


def score_words(score: float) -> str:
    if score >= 0.75:
        return "se parecen mucho"
    if score >= 0.55:
        return "tienen bastante en común"
    if score >= 0.35:
        return "guardan alguna relación"
    if score >= 0.2:
        return "se parecen poco"
    return "casi no se parecen en este modelo"


def pct(score: float) -> str:
    return f"{int(round(score * 100))}%"


def card_by_name(cards, nombre: str):
    return next(c for c in cards if c.nombre == nombre)


def friendly_list(items: list[str], empty: str = "nada destacado") -> str:
    if not items:
        return empty
    clean = [x.replace("_", " ") for x in items]
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} y {clean[1]}"
    return ", ".join(clean[:-1]) + f" y {clean[-1]}"


def show_disclaimer() -> None:
    st.caption(
        "Esto es una herramienta de estudio y reflexión. "
        "No predice el futuro ni da consejos médicos, legales o financieros."
    )


def show_card_image(card, caption: str | None = None) -> None:
    img = ROOT / card.imagen
    if img.exists():
        st.image(str(img), caption=caption or card.nombre, width="stretch")


def study_sources(card) -> tuple[object | None, object | None]:
    jodo = next(
        (s for s in card.significados if "Jodorowsky" in " ".join(s.autores) or "vía del Tarot" in s.fuente),
        None,
    )
    canseco = next(
        (s for s in card.significados if "Canseco" in " ".join(s.autores) or "dilema a la metáfora" in s.fuente.lower()),
        None,
    )
    return jodo, canseco


def show_study_blurbs(card) -> None:
    jodo, canseco = study_sources(card)
    if jodo and (jodo.subtitulo or jodo.esencia):
        st.info(f"**Jodorowsky/Costa:** {jodo.subtitulo or jodo.esencia}")
    if canseco and canseco.esencia:
        st.success(f"**Canseco:** {canseco.esencia}")


def page_home(cards) -> None:
    hero(
        "El Tejido Arcano",
        "Un laboratorio visual para explorar cartas, sentidos y relaciones — con calma, belleza y sin predicciones.",
    )
    show_disclaimer()

    cotd = card_of_the_day(cards=cards)
    card = cotd["card"]
    st.markdown('<span class="tejido-badge">Carta de hoy</span>', unsafe_allow_html=True)
    st.markdown('<hr class="tejido-divider"/>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        show_card_image(card)
    with c2:
        st.markdown(f"## {card.nombre}")
        if cotd["subtitulo"]:
            st.info(cotd["subtitulo"])
        if cotd["esencia"]:
            st.write(cotd["esencia"])
        st.write(f"**Pregunta para hoy:** {cotd['pregunta']}")
        if cotd["companion"]:
            st.write(
                f"Conexión sorprendente del día: **{cotd['companion'].nombre}** "
                f"({score_words(cotd['companion_score'])})."
            )
        st.caption(cotd["disclaimer"])

    st.markdown('<hr class="tejido-divider"/>', unsafe_allow_html=True)
    st.markdown(
        """
**¿Qué quieres explorar?**

1. **Juegos de cartas** — memoria, contraste, oráculo de 1 minuto, tirada-cine  
2. **Mapa neurológico** — cerebro 3D: cartas ↔ regiones (analogía educativa)  
3. **Contar una historia** — tres cartas y un relato posible  
4. **Constelación** — una carta y su cielo cercano (con animación)  
5. **Juego del puente** — adivina quién une dos extremos  
6. **Mirar el mapa** — toda la red en movimiento  
"""
    )


def page_story(cards, profile: str) -> None:
    hero("Contar una historia", "Elige tres cartas. Aparecerá un relato posible — y finales alternativos.")
    show_disclaimer()

    selected = st.multiselect(
        "Tus tres cartas",
        [c.nombre for c in cards],
        default=[cards[0].nombre, cards[8].nombre, cards[16].nombre] if len(cards) > 16 else [c.nombre for c in cards[:3]],
        max_selections=3,
    )
    if len(selected) < 2:
        st.info("Elige al menos 2 cartas (idealmente 3).")
        return

    name_to_id = {c.nombre: c.id for c in cards}
    ids = [name_to_id[n] for n in selected]

    cols = st.columns(len(selected))
    for i, nombre in enumerate(selected):
        with cols[i]:
            show_card_image(card_by_name(cards, nombre))

    if st.button("Crear historia", type="primary"):
        with st.spinner("Tejiendo hipótesis…"):
            story = build_story(ids, cards=cards, profile=profile)
            st.session_state["last_story"] = story
            st.session_state["last_story_ids"] = ids

    story = st.session_state.get("last_story")
    if not story or st.session_state.get("last_story_ids") != ids:
        return

    st.markdown(f"### {story.title}")
    st.markdown(story.opening)
    st.markdown(story.middle)
    st.markdown(story.closing)
    if story.focus_pair:
        st.success(story.focus_pair)
    if story.tension_note:
        st.warning(story.tension_note)

    st.markdown("#### Otros finales posibles")
    st.write(f"- {story.alternate_ending_a}")
    st.write(f"- {story.alternate_ending_b}")

    st.markdown("#### Preguntas para llevarte")
    for q in story.questions:
        st.write(f"- {q}")
    st.caption(story.disclaimer)

    png = export_lamina(
        ids,
        title="Historia — El Tejido Arcano",
        subtitle=story.title,
        story_lines=[story.opening, story.closing, story.disclaimer],
        cards=cards,
    )
    st.download_button(
        "Descargar lámina (PNG)",
        data=png,
        file_name="tejido_arcano_historia.png",
        mime="image/png",
    )


def page_constellation(cards, profile: str, top_k: int, builder: GraphBuilder) -> None:
    hero("Constelación", "Una carta en el centro. Su cielo cercano late, gira y explica cada vínculo.")
    show_disclaimer()

    nombre = st.selectbox("Carta central", [c.nombre for c in cards])
    card = card_by_name(cards, nombre)
    show_nombres = st.toggle("Mostrar nombres en el mapa", value=True)

    with st.spinner("Armando constelación…"):
        focus = constellation_focus(card.id, cards=cards, profile=profile, k=top_k)
        G = builder.build(cards, layer="combined", profile=profile, top_k=top_k)
        # subgrafo: centro + vecinos
        keep = {card.id} | {n["id"] for n in focus["neighbors"]}
        H = G.subgraph(keep).copy()
        fig = build_figure(
            H,
            dim=3,
            color_by="dominant",
            show_labels=show_nombres,
            title=f"Constelación de {card.nombre}",
            preset="constelacion",
            animate=True,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Pulsa **▷ Animar** bajo el grafo para la órbita y el pulso.")

    c1, c2 = st.columns([1, 2])
    with c1:
        show_card_image(card)
    with c2:
        st.markdown(f"### Alrededor de {card.nombre}")
        for n in focus["neighbors"]:
            bits = []
            if n["shared_symbols"]:
                bits.append("símbolos: " + friendly_list(n["shared_symbols"][:4]))
            if n["shared_emotions"]:
                bits.append("emociones: " + friendly_list(n["shared_emotions"][:3]))
            if n["top_dimensions"]:
                bits.append(
                    "fuerza en "
                    + ", ".join(f"{DIM_LABELS.get(d, d)} ({pct(v)})" for d, v in n["top_dimensions"][:2])
                )
            st.markdown(f"**{n['nombre']}** — {score_words(n['score'])} ({pct(n['score'])})")
            for b in bits:
                st.write(f"- {b}")
            for d in n.get("differences") or []:
                st.caption(f"Diferencia: {d}")
            st.divider()
    st.caption(focus["disclaimer"])


def page_bridge_game(cards, profile: str) -> None:
    hero("Juego del puente", "Dos extremos. Una carta oculta los une. ¿Cuál es?")
    show_disclaimer()

    if "bridge_challenge" not in st.session_state:
        st.session_state["bridge_challenge"] = make_bridge_challenge(
            cards=cards, seed=date.today().isoformat() + "-play", profile=profile
        )
        st.session_state["bridge_answered"] = False

    if st.button("Nueva ronda"):
        import time

        st.session_state["bridge_challenge"] = make_bridge_challenge(
            cards=cards, seed=f"{time.time()}", profile=profile
        )
        st.session_state["bridge_answered"] = False
        st.rerun()

    ch = st.session_state["bridge_challenge"]
    by_id = {c.id: c for c in cards}
    start, end = by_id[ch.start_id], by_id[ch.end_id]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Desde**")
        show_card_image(start)
    with c2:
        st.markdown("**¿Puente?**")
        st.write("Elige abajo")
    with c3:
        st.markdown("**Hasta**")
        show_card_image(end)

    options = [by_id[i].nombre for i in ch.options]
    choice = st.radio("Tu respuesta", options, key="bridge_choice")
    if st.button("Comprobar", type="primary"):
        st.session_state["bridge_answered"] = True
        st.session_state["bridge_choice_name"] = choice

    if st.session_state.get("bridge_answered"):
        chosen_id = next(c.id for c in cards if c.nombre == st.session_state["bridge_choice_name"])
        answer = by_id[ch.answer_id]
        path_names = [by_id[i].nombre for i in ch.path]
        if chosen_id == ch.answer_id:
            st.success(f"Sí: **{answer.nombre}** encaja como puente en este modelo.")
        else:
            st.info(
                f"En esta ronda el puente propuesto era **{answer.nombre}**. "
                f"Tu elección también puede tener sentido en otra lectura."
            )
        st.write("Camino revelado: " + " → ".join(f"**{n}**" for n in path_names))
        st.caption("Es un camino del grafo del laboratorio, no una verdad del Tarot.")


def page_map(cards, profile: str, layer: str, top_k: int, builder: GraphBuilder) -> None:
    hero("Mirar el mapa", "La red completa: puntos que respiran, hilos dorados, órbita silenciosa.")
    show_disclaimer()
    vista_3d = st.toggle("Vista en 3D", value=True)
    mostrar_nombres = st.toggle("Mostrar nombres", value=False)
    animar = st.toggle("Activar animación", value=True)
    with st.spinner("Preparando el mapa…"):
        G = builder.build(cards, layer=layer, profile=profile, top_k=top_k)  # type: ignore[arg-type]
        fig = build_figure(
            G,
            dim=3 if vista_3d else 2,
            color_by="community",
            show_labels=mostrar_nombres,
            title="Mapa de relaciones entre cartas",
            preset="noche",
            animate=animar,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        if animar:
            st.caption("Pulsa **▷ Animar** para ver el pulso y el giro de la constelación.")
    m = graph_metrics(G)
    st.success(
        f"**{m['nodes']} cartas**, **{m['edges']} conexiones**, "
        f"**{len(m.get('communities') or [])} grupos**."
    )


def page_card_detail(cards, profile: str, top_k: int, builder: GraphBuilder) -> None:
    hero("Conocer una carta", "Imagen, sentidos posibles y quién orbita cerca.")
    show_disclaimer()
    nombre = st.selectbox("Elige una carta", [c.nombre for c in cards])
    card = card_by_name(cards, nombre)
    col1, col2 = st.columns([1, 1.4])
    with col1:
        show_card_image(card)
    with col2:
        st.markdown(f"### {card.nombre}")
        st.write(f"**{card.nombre_original}** · número **{card.numero}**")
        jodo = next(
            (s for s in card.significados if "Jodorowsky" in " ".join(s.autores) or "vía del Tarot" in s.fuente),
            None,
        )
        canseco = next(
            (s for s in card.significados if "Canseco" in " ".join(s.autores) or "dilema a la metáfora" in s.fuente.lower()),
            None,
        )
        if jodo:
            st.markdown("#### Según *La vía del Tarot*")
            if jodo.subtitulo:
                st.info(jodo.subtitulo)
            if jodo.esencia:
                st.write(jodo.esencia)
            if jodo.en_lectura:
                st.write(jodo.en_lectura)
            if jodo.preguntas:
                st.markdown("**Preguntas**")
                for q in jodo.preguntas:
                    st.write(f"- {q}")
        if canseco:
            st.markdown("#### Según *El tarot: del dilema a la metáfora* (Canseco)")
            if canseco.esencia:
                st.success(f"**Metáfora:** {canseco.esencia}")
            if canseco.preguntas:
                st.write(f"**Dilema:** {canseco.preguntas[0]}")
            if canseco.en_lectura:
                st.write(f"**Escena posible:** {canseco.en_lectura}")
        st.markdown("**Luz:** " + friendly_list(card.palabras_clave.luz))
        st.markdown("**Sombra:** " + friendly_list(card.palabras_clave.sombra))
        st.markdown("**Emociones:** " + friendly_list(card.emociones))
        st.markdown("**Símbolos:** " + friendly_list(card.simbolos))

    G = builder.build(cards, layer="combined", profile=profile, top_k=top_k)
    if card.id in G:
        id_to_name = {c.id: c.nombre for c in cards}
        neigh = sorted(((n, G[card.id][n]["weight"]) for n in G.neighbors(card.id)), key=lambda x: -x[1])[:5]
        st.markdown("### Se relaciona especialmente con")
        for n, w in neigh:
            st.write(f"- **{id_to_name.get(n, n)}** — {score_words(w)} ({pct(w)})")


def page_compare(cards, profile: str) -> None:
    hero("Comparar dos cartas", "Dos imágenes frente a frente: en qué se parecen y en qué no.")
    show_disclaimer()
    c1, c2 = st.columns(2)
    with c1:
        a_name = st.selectbox("Primera", [c.nombre for c in cards], key="cmp_a")
    with c2:
        b_name = st.selectbox("Segunda", [c.nombre for c in cards], index=min(1, len(cards) - 1), key="cmp_b")
    if a_name == b_name:
        st.warning("Elige dos cartas distintas.")
        return
    a, b = card_by_name(cards, a_name), card_by_name(cards, b_name)
    ic1, ic2 = st.columns(2)
    with ic1:
        show_card_image(a)
    with ic2:
        show_card_image(b)
    engine = SimilarityEngine(profile=profile)
    engine.fit_corpus(cards)
    res = engine.compare(a, b, profile=profile)
    st.markdown(f"### {a.nombre} y {b.nombre} {score_words(res.similarity_total)}")
    st.progress(min(max(res.similarity_total, 0.0), 1.0), text=f"Parecido: {pct(res.similarity_total)}")
    exp = res.explanation
    if exp.shared_symbols:
        st.write(f"- Símbolos comunes: **{friendly_list(exp.shared_symbols)}**")
    if exp.shared_emotions:
        st.write(f"- Emociones cercanas: **{friendly_list(exp.shared_emotions)}**")
    if exp.shared_archetypes:
        st.write(f"- Arquetipos: **{friendly_list(exp.shared_archetypes)}**")
    dims = res.dimensions.model_dump()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[DIM_LABELS.get(k, k) for k in dims],
                y=list(dims.values()),
                marker=dict(color="#d4af6a", line=dict(width=0)),
            )
        ],
        layout=go.Layout(
            yaxis=dict(range=[0, 1], title="Parecido", gridcolor="rgba(255,255,255,0.06)"),
            xaxis=dict(tickangle=-20),
            height=360,
            margin=dict(t=10, b=80),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c9c0b4", family="Sora, sans-serif"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def page_spread(cards, profile: str, builder: GraphBuilder) -> None:
    hero("Leer una tirada", "Patrones, puente, tensión… y si quieres, una historia exportable.")
    show_disclaimer()
    selected = st.multiselect(
        "Cartas",
        [c.nombre for c in cards],
        default=[cards[0].nombre, cards[8].nombre, cards[16].nombre] if len(cards) > 16 else [c.nombre for c in cards[:3]],
        max_selections=5,
    )
    if not st.button("Analizar", type="primary") or len(selected) < 2:
        return
    name_to_id = {c.nombre: c.id for c in cards}
    id_to_name = {c.id: c.nombre for c in cards}
    ids = [name_to_id[n] for n in selected]
    cols = st.columns(len(selected))
    for i, n in enumerate(selected):
        with cols[i]:
            show_card_image(card_by_name(cards, n))
    result = SpreadAnalyzer(builder).analyze(ids, cards=cards, profile=profile)
    dens = result.metrics.get("density") or {}
    if result.bridge_card:
        st.write(f"- **Puente:** {id_to_name.get(result.bridge_card['card_id'])}")
    if dens:
        st.write(f"- Similitud media: {pct(dens.get('mean_similarity', 0))}")
    for h in result.narrative_hypotheses:
        st.write(f"- {h}")

    # also offer story + lamina
    story = build_story(ids, cards=cards, profile=profile)
    with st.expander("Ver como historia"):
        st.write(story.opening)
        st.write(story.middle)
        st.write(story.closing)
    png = export_lamina(ids, title="Tirada — El Tejido Arcano", subtitle=" · ".join(selected), story_lines=[story.closing], cards=cards)
    st.download_button("Descargar lámina", data=png, file_name="tirada.png", mime="image/png")


def page_path(cards, profile: str, top_k: int, builder: GraphBuilder) -> None:
    hero("Buscar un camino", "De una carta a otra, pasando por puentes del modelo.")
    show_disclaimer()
    c1, c2 = st.columns(2)
    with c1:
        a = st.selectbox("Desde", [c.nombre for c in cards], key="pa")
    with c2:
        b = st.selectbox("Hasta", [c.nombre for c in cards], index=min(16, len(cards) - 1), key="pb")
    if not st.button("Buscar", type="primary") or a == b:
        return
    name_to_id = {c.nombre: c.id for c in cards}
    id_to_name = {c.id: c.nombre for c in cards}
    G = builder.build(cards, layer="combined", profile=profile, top_k=top_k)
    path = find_hidden_path(name_to_id[a], name_to_id[b], G, builder.engine, {c.id: c for c in cards}, profile=profile)
    if not path:
        st.error("Sin camino con estos ajustes.")
        return
    st.write(" → ".join(f"**{id_to_name.get(x, x)}**" for x in path["sequence"]))


def page_search(cards) -> None:
    hero("Buscar por idea", "Escribe un sentimiento o tema y aparecen cartas cercanas.")
    show_disclaimer()
    q = st.text_input("Idea", placeholder="liberación, miedo, cuidado…")
    if not q.strip():
        return
    qn = q.lower().strip()
    hits = []
    for c in cards:
        blob = " ".join(
            c.palabras_clave.luz + c.palabras_clave.sombra + c.arquetipos + c.emociones + [s.esencia for s in c.significados]
        ).lower()
        if qn in blob or qn in c.nombre.lower():
            hits.append(c)
    if not hits:
        st.warning("Sin resultados.")
        return
    for c in hits:
        with st.expander(c.nombre):
            cols = st.columns([1, 2])
            with cols[0]:
                show_card_image(c)
            cols[1].write("Luz: " + friendly_list(c.palabras_clave.luz))


def page_ml(cards) -> None:
    hero("Descubrimientos", "El modelo sugiere: por visión, por texto o por la red.")
    show_disclaimer()
    lab = get_ml_lab()
    id_to_name = {c.id: c.nombre for c in cards}
    name_to_id = {c.nombre: c.id for c in cards}
    nombre = st.selectbox("Carta", [c.nombre for c in cards], key="mlc")
    modo = st.radio(
        "Tipo de parecido",
        ["Combinado (recomendado)", "Solo imagen", "Solo significados", "Solo red"],
    )
    mode_map = {
        "Combinado (recomendado)": "combinado",
        "Solo imagen": "vision",
        "Solo significados": "texto",
        "Solo red": "grafo",
    }
    if st.button("Buscar parecidos", type="primary"):
        recs = lab.recommend(name_to_id[nombre], mode=mode_map[modo], k=5)  # type: ignore[arg-type]
        for r in recs:
            st.write(f"- **{id_to_name[r.card_id]}** ({pct(min(r.score, 1.0))})")
            for reason in r.reasons:
                st.caption(reason)


def page_games(cards) -> None:
    hero(
        "Juegos de cartas",
        "El tarot como pasatiempo serio: imágenes, dilemas y metáforas. "
        "Inspirado en Jodorowsky y en Canseco (del dilema a la metáfora).",
    )
    show_disclaimer()
    st.caption("El foco son siempre las cartas — no predicciones.")

    by_id = {c.id: c for c in cards}
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Memoria arcana", "¿Cuál no encaja?", "Oráculo de 1 minuto", "Tirada-cine"]
    )

    with tab1:
        st.write("Empareja cada **carta** con su **hilo de sentido** (Jodorowsky / esencia).")
        if st.button("Nueva memoria", key="mem_new"):
            st.session_state["memory"] = make_memory_round(cards, n_pairs=4, seed=str(date.today()) + str(st.session_state.get("_n", 0)))
            st.session_state["mem_open"] = []
            st.session_state["mem_matched"] = set()
            st.session_state["_n"] = st.session_state.get("_n", 0) + 1
        if "memory" not in st.session_state:
            st.session_state["memory"] = make_memory_round(cards, n_pairs=4)
            st.session_state["mem_open"] = []
            st.session_state["mem_matched"] = set()

        mem = st.session_state["memory"]
        matched = st.session_state["mem_matched"]
        opened = st.session_state["mem_open"]

        cols = st.columns(4)
        for i, tile in enumerate(mem.tiles):
            col = cols[i % 4]
            with col:
                is_match = tile["ref"] in matched
                is_open = tile["id"] in opened or is_match
                if tile["kind"] == "card" and is_open:
                    show_card_image(by_id[tile["ref"]], caption=tile["label"])
                elif is_open:
                    st.info(tile["label"])
                else:
                    if st.button("✧", key=f"tile_{tile['id']}", use_container_width=True):
                        if tile["id"] not in opened and tile["ref"] not in matched:
                            opened.append(tile["id"])
                            if len(opened) == 2:
                                a = next(t for t in mem.tiles if t["id"] == opened[0])
                                b = next(t for t in mem.tiles if t["id"] == opened[1])
                                if a["ref"] == b["ref"] and a["kind"] != b["kind"]:
                                    matched.add(a["ref"])
                                    opened.clear()
                                else:
                                    # keep brief reveal then reset on next run via flag
                                    st.session_state["mem_mismatch"] = True
                            st.session_state["mem_open"] = opened
                            st.session_state["mem_matched"] = matched
                            st.rerun()
                if is_match:
                    st.caption("✓")

        if st.session_state.get("mem_mismatch") and len(opened) >= 2:
            st.warning("No era pareja. Mira bien las cartas…")
            if st.button("Seguir"):
                st.session_state["mem_open"] = []
                st.session_state["mem_mismatch"] = False
                st.rerun()

        if len(matched) >= len(mem.pairs):
            st.success("¡Completaste el círculo de cartas!")

    with tab2:
        st.write("Tres cartas comparten un **hilo** (elemento). ¿Cuál quiebra el patrón?")
        if st.button("Nueva ronda", key="odd_new") or "odd" not in st.session_state:
            st.session_state["odd"] = make_odd_one_out(cards)
            st.session_state["odd_answered"] = False
        odd = st.session_state["odd"]
        opts = [by_id[i] for i in odd.card_ids]
        cols = st.columns(4)
        for i, c in enumerate(opts):
            with cols[i]:
                show_card_image(c)
        choice = st.radio("La que no encaja es…", [c.nombre for c in opts], key="odd_choice")
        if st.button("Comprobar", key="odd_check", type="primary"):
            st.session_state["odd_answered"] = True
        if st.session_state.get("odd_answered"):
            chosen = next(c for c in opts if c.nombre == choice)
            if chosen.id == odd.odd_id:
                st.success(f"Exacto. Regla de la ronda: {odd.rule}.")
            else:
                st.info(f"En esta ronda era **{by_id[odd.odd_id].nombre}**. {odd.explanation}")
            st.caption(odd.explanation)

    with tab3:
        st.write(
            "Un minuto con **una sola carta**: dilema → metáfora "
            "(Canseco) y eco de *La vía del Tarot*."
        )
        if st.button("Sacar carta", type="primary", key="oracle_draw"):
            st.session_state["oracle"] = minute_oracle(cards, seed=f"{date.today()}-{st.session_state.get('_n',0)}")
            st.session_state["_n"] = st.session_state.get("_n", 0) + 1
        if "oracle" not in st.session_state:
            st.session_state["oracle"] = minute_oracle(cards)
        o = st.session_state["oracle"]
        c1, c2 = st.columns([1, 2])
        with c1:
            show_card_image(o.card)
        with c2:
            st.markdown(f"### {o.card.nombre}")
            st.markdown(f"**Dilema:** {o.dilema}")
            st.success(f"**Metáfora:** {o.metafora}")
            st.write(f"**Pregunta:** {o.pregunta}")
            with st.expander("Escuchar dos voces de estudio"):
                st.write(f"**Jodorowsky/Costa:** {o.voz_jodorowsky}")
                st.write(f"**Canseco:** {o.voz_canseco}")
                st.write(f"**Plano posible:** {o.cinematic}")
            st.caption(o.disclaimer)

    with tab4:
        st.write(
            "Tres cartas = tres actos. "
            "Como una cinematografía de imágenes (eco de Canseco / Calvino)."
        )
        mode = st.radio("¿Cómo armar la película?", ["Al azar con el mazo", "Elegir yo las tres"], horizontal=True)
        ids = None
        if mode.startswith("Elegir"):
            names = st.multiselect(
                "Tres cartas",
                [c.nombre for c in cards],
                max_selections=3,
                key="cine_pick",
            )
            if len(names) == 3:
                ids = [next(c.id for c in cards if c.nombre == n) for n in names]
        if st.button("Proyectar tirada-cine", type="primary"):
            if mode.startswith("Elegir") and (not ids or len(ids) < 3):
                st.warning("Elige exactamente 3 cartas.")
            else:
                st.session_state["cinema"] = cinema_spread(card_ids=ids, cards=cards)
        if "cinema" in st.session_state:
            cine = st.session_state["cinema"]
            st.markdown(f"### {cine.title}")
            cols = st.columns(3)
            for i, act in enumerate(cine.acts):
                with cols[i]:
                    show_card_image(by_id[act["card_id"]])
                    st.markdown(f"**{act['role']}** — {act['beat']}")
                    if act.get("metafora"):
                        st.caption(act["metafora"])
                    st.write(act["line"])
            st.info(cine.alternate_cut)
            st.caption(cine.disclaimer)
            png = export_lamina(
                [a["card_id"] for a in cine.acts],
                title="Tirada-cine — El Tejido Arcano",
                subtitle=cine.title,
                story_lines=[a["line"] for a in cine.acts] + [cine.disclaimer],
                cards=cards,
            )
            st.download_button("Descargar lámina", data=png, file_name="tirada_cine.png", mime="image/png")


def page_identity(cards) -> None:
    hero(
        "Quién eres",
        "Test de afinidad, carta guía y mapa personal de 22 arcanos: juego simbólico, no diagnóstico ni destino.",
    )
    show_disclaimer()
    by_id = {c.id: c for c in cards}

    tab_quiz, tab_guide, tab_spread = st.tabs(["Test arcano", "Carta guía", "Mapa de 22 cartas"])

    with tab_quiz:
        st.write(
            "Responde como en una pequeña aventura: cada opción suma afinidad con arcanos mayores. "
            "El resultado es una invitación narrativa, no una etiqueta psicológica."
        )
        with st.form("personality_quiz"):
            answers: dict[str, str] = {}
            for q in QUESTIONS:
                labels = [o.text for o in q.options]
                label_to_id = {o.text: o.id for o in q.options}
                choice = st.radio(q.text, labels, key=f"quiz_{q.id}")
                answers[q.id] = label_to_id[choice]
            submitted = st.form_submit_button("Revelar carta del test", type="primary")

        if submitted:
            st.session_state["personality_quiz_result"] = score_quiz(answers, cards=cards)

        result = st.session_state.get("personality_quiz_result")
        if result:
            card = by_id[result.primary_id]
            st.markdown(f"### Tu carta del test: {card.nombre}")
            c1, c2 = st.columns([1, 2], gap="large")
            with c1:
                show_card_image(card)
            with c2:
                st.write(result.explanation)
                st.write(result.invitation)
                show_study_blurbs(card)
                if result.runner_up_ids:
                    runner_names = ", ".join(by_id[i].nombre for i in result.runner_up_ids if i in by_id)
                    st.caption(f"Cartas secundarias: {runner_names}.")
                st.caption(result.disclaimer)

    with tab_guide:
        st.write(
            "Método: suma de dígitos de la fecha en formato AAAAMMDD y reducción por módulo 22 "
            "(El Loco = 0). Es numerología lúdica para estudiar cartas, no predicción."
        )
        born = st.date_input("Fecha de nacimiento", value=date(1990, 5, 17), key="guide_birthdate")
        guide = guide_card_from_birthdate(born, cards=cards)
        card = by_id[guide.card_id]
        c1, c2 = st.columns([1, 2], gap="large")
        with c1:
            show_card_image(card)
        with c2:
            st.markdown(f"### Carta guía: {card.nombre}")
            st.write(guide.explanation)
            show_study_blurbs(card)
            st.caption(guide.method)
            st.caption(guide.disclaimer)

    with tab_spread:
        st.write(
            "El mapa ordena los 22 arcanos de forma determinista desde tu fecha. "
            "Si ya hiciste el test, puedes usar su carta como modificador para resaltarla dentro del recorrido."
        )
        born_spread = st.date_input("Fecha para el mapa", value=date(1990, 5, 17), key="spread_birthdate")
        quiz_result = st.session_state.get("personality_quiz_result")
        use_quiz = st.checkbox("Combinar con la carta del test", value=bool(quiz_result), disabled=not bool(quiz_result))
        quiz_card_id = quiz_result.primary_id if (use_quiz and quiz_result) else None
        spread = personal_spread_from_birthdate(born_spread, cards=cards, quiz_card_id=quiz_card_id)
        st.caption(spread.method)

        for row_start in range(0, len(spread.positions), 2):
            cols = st.columns(2, gap="large")
            for col, pos in zip(cols, spread.positions[row_start : row_start + 2]):
                card = by_id[pos.card_id]
                with col:
                    title = f"{pos.number}. {pos.role} — {card.nombre}"
                    with st.expander(("✦ " if pos.highlighted else "") + title, expanded=pos.highlighted):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            show_card_image(card)
                        with c2:
                            st.write(pos.note)
                            jodo, canseco = study_sources(card)
                            if jodo and jodo.preguntas:
                                st.caption(f"Pregunta de estudio: {jodo.preguntas[0]}")
                            elif canseco and canseco.preguntas:
                                st.caption(f"Pregunta de estudio: {canseco.preguntas[0]}")
        st.caption(spread.disclaimer)


def page_neuro(cards) -> None:
    hero(
        "Mapa neurológico",
        "Arcanos mayores como metáforas de regiones y circuitos. "
        "Inspirado en Brain Facts (SfN) y en la neurobiología de la imaginación.",
    )
    st.warning(map_disclaimer())
    show_disclaimer()

    regions = load_regions()
    mode = st.radio(
        "Explorar por…",
        ["Región cerebral", "Carta del tarot"],
        horizontal=True,
    )

    highlight_region = None
    highlight_card = None
    detail = None

    if mode.startswith("Región"):
        labels = {r.nombre: r.id for r in regions.values()}
        choose = st.selectbox("Región", list(labels.keys()))
        highlight_region = labels[choose]
        detail = explore_by_region(highlight_region, cards)
    else:
        name = st.selectbox("Carta", [c.nombre for c in cards])
        card = card_by_name(cards, name)
        highlight_card = card.id
        detail = explore_by_card(card)

    fig = build_brain_figure(
        cards,
        highlight_region=highlight_region,
        highlight_card=highlight_card,
    )
    st.plotly_chart(fig, use_container_width=True)

    if detail and detail.get("error"):
        st.error(detail["error"])
        return

    if mode.startswith("Región") and detail:
        reg = detail["region"]
        st.markdown(f"### {reg.nombre}")
        st.caption(reg.sistema)
        st.write(reg.hecho_breve)
        with st.expander("Más contexto (estudio)"):
            st.write(reg.detalle)
            notes = detail.get("sources") or {}
            if notes.get("brain_facts"):
                st.caption(
                    f"Fuente: {notes['brain_facts']['title']} — {notes['brain_facts']['note']}"
                )
            if notes.get("drubach_imagination"):
                st.caption(
                    f"Fuente: {notes['drubach_imagination']['title']} — {notes['drubach_imagination']['note']}"
                )
        st.markdown("#### Cartas que habitan esta región")
        for item in detail["cards"]:
            c = item["card"]
            cols = st.columns([1, 3])
            with cols[0]:
                show_card_image(c)
            with cols[1]:
                badge = "principal" if item["role"] == "principal" else "resonante"
                st.markdown(f"**{c.nombre}** · _{badge}_")
                st.write(item["rationale"])
                st.caption(item["pregunta"])
    elif detail:
        primary = detail["primary"]
        c = card_by_name(cards, detail["card_nombre"])
        left, right = st.columns([1, 2])
        with left:
            show_card_image(c)
        with right:
            st.markdown(f"### {c.nombre} → {primary.nombre}")
            st.caption(primary.sistema)
            st.write(detail["rationale"])
            st.info(f"**Hecho Brain Facts / estudio:** {primary.hecho_breve}")
            st.success(f"**Pregunta:** {detail['pregunta']}")
            if detail.get("secondary"):
                st.write(
                    "También resuena con: "
                    + ", ".join(r.nombre for r in detail["secondary"])
                )
            with st.expander("Voces del tarot (Jodorowsky · Canseco)"):
                if detail.get("voz_jodorowsky"):
                    st.write(f"**Jodorowsky/Costa:** {detail['voz_jodorowsky']}")
                if detail.get("voz_canseco"):
                    st.write(f"**Canseco:** {detail['voz_canseco']}")
                st.write(primary.detalle)


def main() -> None:
    cards = cards_list()
    builder = get_builder()
    st.sidebar.markdown(
        '<div class="tejido-brand" style="font-family:Fraunces,serif;font-size:1.35rem;color:#d4af6a;">El Tejido Arcano</div>'
        '<div style="color:#c9c0b4;font-size:0.85rem;margin:0.25rem 0 1rem;">Explora · juega · reflexiona</div>',
        unsafe_allow_html=True,
    )
    seccion = st.sidebar.radio(
        "¿Qué quieres hacer?",
        [
            "Inicio",
            "Quién eres",
            "Juegos de cartas",
            "Mapa neurológico",
            "Contar una historia",
            "Constelación",
            "Juego del puente",
            "Mirar el mapa",
            "Conocer una carta",
            "Comparar dos cartas",
            "Leer una tirada",
            "Buscar un camino",
            "Buscar por idea",
            "Descubrimientos",
        ],
    )
    with st.sidebar.expander("Ajustes (opcional)", expanded=False):
        modo_label = st.selectbox("¿Cómo comparar?", list(MODOS.keys()))
        vista_label = st.selectbox("Tipo de conexión", list(VISTAS.keys()))
        intensidad = st.slider("Conexiones por carta", 2, 8, 4)
    profile, layer, top_k = MODOS[modo_label], VISTAS[vista_label], intensidad

    pages = {
        "Inicio": lambda: page_home(cards),
        "Quién eres": lambda: page_identity(cards),
        "Juegos de cartas": lambda: page_games(cards),
        "Mapa neurológico": lambda: page_neuro(cards),
        "Contar una historia": lambda: page_story(cards, profile),
        "Constelación": lambda: page_constellation(cards, profile, top_k, builder),
        "Juego del puente": lambda: page_bridge_game(cards, profile),
        "Mirar el mapa": lambda: page_map(cards, profile, layer, top_k, builder),
        "Conocer una carta": lambda: page_card_detail(cards, profile, top_k, builder),
        "Comparar dos cartas": lambda: page_compare(cards, profile),
        "Leer una tirada": lambda: page_spread(cards, profile, builder),
        "Buscar un camino": lambda: page_path(cards, profile, top_k, builder),
        "Buscar por idea": lambda: page_search(cards),
        "Descubrimientos": lambda: page_ml(cards),
    }
    pages[seccion]()


if __name__ == "__main__":
    main()
