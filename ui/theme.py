"""Tema visual y animaciones CSS para Streamlit — El Tejido Arcano."""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Sora:wght@300;400;500;600&display=swap');

:root {
  --ink: #100e14;
  --ink-2: #1a1620;
  --panel: #221c28;
  --line: rgba(212, 175, 106, 0.28);
  --gold: #d4af6a;
  --gold-soft: #e8d2a0;
  --mist: #c9c0b4;
  --paper: #f3ebe0;
  --accent-teal: #6a9e98;
}

html, body, [class*="css"] {
  font-family: "Sora", sans-serif !important;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(212, 175, 106, 0.14), transparent 55%),
    radial-gradient(900px 500px at 90% 0%, rgba(106, 158, 152, 0.12), transparent 50%),
    radial-gradient(700px 400px at 50% 100%, rgba(90, 60, 40, 0.25), transparent 55%),
    linear-gradient(165deg, #0c0a10 0%, #16121a 45%, #121018 100%) !important;
  color: var(--paper);
}

/* subtle star dust */
.stApp::before {
  content: "";
  pointer-events: none;
  position: fixed;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.35), transparent),
    radial-gradient(1px 1px at 30% 70%, rgba(255,255,255,0.22), transparent),
    radial-gradient(1.5px 1.5px at 70% 30%, rgba(212,175,106,0.45), transparent),
    radial-gradient(1px 1px at 85% 60%, rgba(255,255,255,0.2), transparent),
    radial-gradient(1px 1px at 55% 15%, rgba(255,255,255,0.28), transparent);
  opacity: 0.55;
  animation: drift 48s linear infinite;
  z-index: 0;
}

@keyframes drift {
  from { transform: translateY(0); }
  to { transform: translateY(-40px); }
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes softPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 106, 0.0); }
  50% { box-shadow: 0 0 0 8px rgba(212, 175, 106, 0.08); }
}

@keyframes shimmer {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

section.main > div {
  animation: fadeUp 0.55s ease-out both;
}

h1, h2, h3, .tejido-brand {
  font-family: "Fraunces", serif !important;
  letter-spacing: 0.01em;
  color: var(--paper) !important;
}

h1 {
  font-weight: 700 !important;
  font-size: 2.35rem !important;
  background: linear-gradient(100deg, #f7efdf, #d4af6a 55%, #f3ebe0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent !important;
}

.tejido-hero {
  position: relative;
  padding: 1.4rem 1.6rem 1.5rem;
  border: 1px solid var(--line);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(34,28,40,0.92), rgba(18,16,24,0.88));
  animation: fadeUp 0.7s ease-out both, softPulse 5.5s ease-in-out infinite;
  margin-bottom: 1.2rem;
}

.tejido-hero .eyebrow {
  font-family: "Sora", sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.72rem;
  color: var(--gold);
  margin-bottom: 0.35rem;
}

.tejido-kicker {
  color: var(--mist);
  font-size: 1.02rem;
  max-width: 42rem;
  line-height: 1.55;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #140f18 0%, #1b1520 100%) !important;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] * {
  color: var(--paper) !important;
}

div[data-testid="stSidebarNav"] {
  padding-top: 0.5rem;
}

.stRadio > label, .stSelectbox label, .stSlider label {
  color: var(--gold-soft) !important;
  font-weight: 500 !important;
}

.stButton > button {
  border-radius: 999px !important;
  border: 1px solid var(--gold) !important;
  background: linear-gradient(120deg, #2a2218, #3a2e20) !important;
  color: var(--gold-soft) !important;
  font-family: "Sora", sans-serif !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em;
  transition: transform 0.2s ease, box-shadow 0.25s ease, background 0.25s ease !important;
}

.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(212, 175, 106, 0.18);
  background: linear-gradient(120deg, #3a2e20, #4a3a28) !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(120deg, #c4a05a, #8a6a35) !important;
  color: #1a1208 !important;
  border: none !important;
}

div[data-testid="stImage"] img {
  border-radius: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  animation: fadeUp 0.65s ease-out both;
}

div[data-testid="stImage"] img:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow: 0 18px 48px rgba(212, 175, 106, 0.16);
}

div[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 14px !important;
  background: rgba(26, 22, 32, 0.7) !important;
  animation: fadeUp 0.5s ease-out both;
}

div[data-testid="stAlert"] {
  border-radius: 12px !important;
  animation: fadeUp 0.45s ease-out both;
}

div[data-testid="stMetric"] {
  background: rgba(26, 22, 32, 0.65);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.75rem 1rem;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.4rem;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 999px;
  background: rgba(255,255,255,0.03);
  color: var(--mist) !important;
}

.stTabs [aria-selected="true"] {
  background: rgba(212, 175, 106, 0.16) !important;
  color: var(--gold-soft) !important;
}

.tejido-divider {
  height: 1px;
  border: 0;
  margin: 1.4rem 0;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0.55;
}

.tejido-badge {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--line);
  color: var(--gold-soft);
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.plotly-graph-div, .stPlotlyChart {
  animation: fadeUp 0.75s ease-out both;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--line);
}

footer { visibility: hidden; }
"""


def inject_theme() -> None:
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "El Tejido Arcano") -> None:
    st.markdown(
        f"""
        <div class="tejido-hero">
          <div class="eyebrow">{eyebrow}</div>
          <div class="tejido-brand" style="font-family:Fraunces,serif;font-size:2rem;font-weight:700;color:#f3ebe0;margin-bottom:0.4rem;">{title}</div>
          <div class="tejido-kicker">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
