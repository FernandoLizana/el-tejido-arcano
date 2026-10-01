# Arquitectura — ArcanaGraph Lab

## Vista general

```
Imágenes (cartas/) + ADN JSON (data/cards/)
        │
        ▼
┌───────────────────┐
│ color_pipeline    │  LAB, ΔE2000, % , histograma
└─────────┬─────────┘
          │
┌─────────▼─────────┐     ┌──────────────────┐
│ SimilarityEngine  │◄────│ weights profiles │
│ (8 dimensiones)   │     └──────────────────┘
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│ GraphBuilder      │  top-k / threshold / mutual
│ capas + NetworkX  │
└─────────┬─────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
 Métricas    SpreadAnalyzer / hidden path
    │
    ├─► Plotly (visualization/)
    ├─► FastAPI (api/)
    └─► Streamlit (ui/)
```

## Capas

| Capa | Responsabilidad |
|------|-----------------|
| `schemas` | Contratos Pydantic |
| `core` | Dominio puro |
| `visualization` | Presentación gráfica |
| `api` / `ui` | Interfaces |
| `data` | ADN, taxonomías, cache, runs |
| `config` | Parámetros versionables |

## Decisiones

1. **FastAPI + Streamlit** porque no existía frontend; coherente con Python científico.
2. **TF-IDF default** para embeddings locales sin descargas pesadas.
3. **Conservar `cartas/`** y `tarot_grafo.py` como migración suave.
4. **Top-k=4** por defecto para evitar el clique del prototipo.
