# Auditoría del proyecto — El Tejido Arcano / ArcanaGraph Lab

**Fecha:** 2026-07-13  
**Alcance:** repositorio `Grafos` (estado pre-migración)  
**Objetivo:** evolucionar el prototipo cromático a una plataforma experimental multidimensional sin reescritura total.

---

## 1. Resumen del sistema actual

El proyecto es un **script exploratorio monolítico** (`tarot_grafo.py`, ~117 líneas) que:

1. Lee imágenes PNG de `cartas/` (22 Arcanos Mayores).
2. Extrae 3 colores vía K-Means (`sklearn`, `random_state=42`).
3. Construye un grafo no dirigido NetworkX: arista si **cualquier** par de colores entre dos cartas tiene distancia euclídea RGB &lt; 50.
4. Visualiza el grafo en Plotly 3D (`fig.show()`), coloreando nodos con el primer centroide K-Means.

No hay backend, API, frontend web, base de datos, tests, README ni `requirements.txt`. Existe un `env/` local (Python 3.13) y un video demo (`video_grafos.mp4`, ~10 MB).

---

## 2. Arquitectura detectada

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
│ cartas/*.png│ --> │ KMeans RGB   │ --> │ NetworkX    │ --> │ Plotly 3D  │
│ (22 mayores)│     │ k=3, seed=42 │     │ umbral=50   │     │ fig.show() │
└─────────────┘     └──────────────┘     └─────────────┘     └────────────┘
         Todo en un solo proceso: tarot_grafo.py (top-level)
```

| Capa | Estado |
|------|--------|
| Datos / ADN | Inexistente (solo filenames) |
| Dominio | Ausente |
| Persistencia | Ninguna |
| API | Ninguna |
| UI | Solo ventana Plotly |
| Tests | Ninguno |
| Docs | Ninguna |

---

## 3. Componentes reutilizables

| Componente | Ubicación | Decisión |
|------------|-----------|----------|
| Imágenes PNG 22 mayores | `cartas/` | **Conservar**; enlazar desde `assets/cards/rws/` o migrar por script |
| Extracción K-Means base | `tarot_grafo.py` → `extraer_colores` | **Refactorizar** a módulo cromático (seed, k, bordes, LAB) |
| Grafo NetworkX | lógica de nodos/edges | **Extender** a multicapa + top-k |
| Visualización Plotly 3D | traces Scatter3d | **Mejorar** (hover, pesos, comunidades); mantener Plotly |
| Semilla 42 | KMeans + spring_layout | **Conservar** como default en config |
| Venv + deps instaladas | `env/` | Reutilizar; añadir deps nuevas vía `requirements.txt` |
| Script legacy | `tarot_grafo.py` | **Conservar** como entrypoint de compatibilidad |

---

## 4. Problemas encontrados

1. **Densidad extrema (~86%)**: umbral RGB 50 + comparación 3×3 produce un casi-clique; el grafo es ilegible.
2. **“Color dominante” incorrecto**: se usa `cluster_centers_[0]`, no el cluster con más píxeles.
3. **Distancia RGB** no perceptual; sin CIELAB / ΔE.
4. **Sin porcentajes** de cada color; sin luminosidad/saturación/temperatura.
5. **Fondo/bordes** posiblemente contaminan la paleta (sin máscara ni crop).
6. **Sin ADN simbólico**, taxonomías ni embeddings.
7. **Sin pesos explicables** ni perfiles de similitud.
8. **Labels 3D** (`markers+text`) saturan la escena.
9. **Prints** en lugar de logging; sin `if __name__ == "__main__"`.
10. **Sin reproducibilidad documentada** de corridas (más allá de seed).
11. **Sin requirements.txt** → no portable.
12. **venv en el árbol** → no debería versionarse.

---

## 5. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Reescritura total | Pérdida de compatibilidad | Mantener `tarot_grafo.py` + script de migración |
| Grafo denso ilegible | UX inútil | top-k / umbral / mutual top-k |
| Dependencias pesadas (sentence-transformers) | Instalación lenta / fallos offline | TF-IDF local como default; interface pluggable |
| ADN incompleto / subjetivo | Sesgo interpretativo | Taxonomías + disclaimer ético + origen/confianza por atributo |
| SobreAlcance 78 cartas | Retraso | Iteración 1: 22 mayores; esquema listo para menores |
| Carpeta sincronizada en la nube + venv | I/O lento | Preferir copia de trabajo local fuera del sync |

---

## 6. Propuesta de arquitectura futura

```
arcanagraph/
  schemas/          # Pydantic CardDNA, SimilarityResult, SpreadResult
  core/
    color/          # pipeline cromático (LAB, ΔE, histograma)
    embeddings/     # Local / TF-IDF / Optional API
    similarity/     # motor multidimensional + pesos
    graph/          # construcción multicapa, top-k, metrics
    spread/         # analizador de tiradas + camino oculto
  visualization/    # Plotly 2D/3D mejorado
  api/              # FastAPI (nuevo; no existía stack web)
  ui/               # Streamlit lab (nuevo; coherente con prototipo científico)
data/
  cards/            # ADN JSON por carta
  taxonomies/       # vocabularios controlados
  cache/            # embeddings + features
  processing_runs/  # metadatos de reproducibilidad
config/             # YAML pesos, perfiles, pipeline
scripts/            # migración, validación, rebuild
tests/
docs/
```

**Separación:** dominio (`core`, `schemas`) · infraestructura (cache, I/O) · API · presentación (Streamlit + Plotly).

**Decisión UI/API:** no había frontend. Se introduce **FastAPI + Streamlit** por alineación con Python científico existente y Plotly, sin forzar React.

---

## 7. Plan por fases (iteración 1 vs posterior)

| Fase | Iteración 1 | Posterior |
|------|-------------|-----------|
| 1 Auditoría | ✅ este documento | Actualizar tras releases |
| 2 ADN simbólico | 22 mayores + taxonomías + validación | Menores + multi-mazo completo |
| 3 Cromático | LAB + ΔE + % + bordes opc. | EMD completo, máscaras ML |
| 4 Motor similitud | 8 dims + perfiles YAML | UI live tuning avanzada |
| 5 Semántica | TF-IDF + interface abstracta | sentence-transformers opcional |
| 6 Grafo multicapa | Combinado + capas + top-k | MST, Leiden, grafo personal |
| 7 Métricas grafo | Degree, betweenness, closeness, pagerank, clustering, Louvain | Explicaciones NL más ricas |
| 8 Métricas Tejido | Resonancia, densidad, entropía, puente, ausentes, camino, tensión, narrativa básica | Pulido UX |
| 9–10 Tiradas / camino | 3 cartas + hidden path básico | Cruz Celta, contraste |
| 11 Comparador mazos | Arquitectura + stub RWS | Marsella annotado |
| 12 Tiradas personales | Schema + SQLite opcional stub | App completa + privacy UX |
| 13–14 UI / viz | Streamlit páginas clave + Plotly | Presets avanzados |
| 15–16 API / persistencia | Endpoints core + cache JSON/SQLite ligero | Migraciones formales |
| 17 Importación | Migrador desde `cartas/` + validate | Editor ADN GUI |
| 18–20 Tests / repro / docs | Suite mínima + README + docs | Cobertura amplia |

---

## 8. Archivos que serán modificados

| Archivo | Cambio |
|---------|--------|
| `tarot_grafo.py` | Wrapper de compatibilidad → delega a pipeline nuevo o documenta deprecación suave |
| (ningún otro archivo de producción previo) | N/A |

---

## 9. Archivos nuevos (iteración 1)

Ver árbol en `docs/ARQUITECTURA.md`. Principales:

- `docs/*` — auditoría, arquitectura, modelo, similitud, métricas, tiradas, guías, roadmap
- `schemas/card_schema.py` — ADN Pydantic
- `data/cards/*.json` — 22 mayores
- `data/taxonomies/*.json`
- `config/similarity_weights.yaml`, `config/pipeline.yaml`
- `core/**` — color, embeddings, similarity, graph, spread, metrics
- `visualization/plotly_graph.py`
- `api/main.py`
- `ui/app.py` (Streamlit)
- `scripts/migrate_legacy_cartas.py`, `scripts/validate_card_data.py`, `scripts/rebuild_graph.py`
- `tests/**`
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`

---

## 10.Checklist de inspección (respuestas)

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | Estructura | Flat: script + cartas + env + video |
| 2 | Módulos reutilizables | Imágenes, idea KMeans, Plotly, NetworkX, seed |
| 3 | Deuda técnica | Monolito, densidad, RGB, sin ADN, sin tests |
| 4 | Duplicación | Ninguna (código único) |
| 5 | Formato colores | Solo RGB enteros en memoria; HEX solo para Plotly |
| 6 | Aristas | Binarias por umbral RGB; sin peso |
| 7 | Reproducibilidad | Seed 42 en KMeans y layout; resto no versionado |
| 8 | Seed KMeans | Sí, `random_state=42` |
| 9 | Normalización imagen | `convert("RGB").resize((100,100))` — sin crop de bordes |
| 10 | Contaminación fondo | Probable; sin máscara |
| 11 | Frontend | No existe |
| 12 | Backend/API | Solo script |
| 13 | Plotly | Interactivo en runtime (`show`), no HTML exportado |

---

## 11. Decisión ética (desde el diseño)

El sistema se presenta como **laboratorio experimental / herramienta de estudio**. Las métricas describen la estructura del modelo y los datos anotados, no verdades universales del Tarot ni predicciones.
