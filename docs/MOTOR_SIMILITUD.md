# Motor de similitud

Archivo: `core/similarity_engine.py`  
Pesos: `config/similarity_weights.yaml`

## Dimensiones

| Dimensión | Método |
|-----------|--------|
| color | Emparejamiento ponderado ΔE2000 sobre paletas LAB |
| symbols / archetypes / emotions / elements / narrative | Jaccard |
| numerology | Cercanía de número y reducción digital |
| semantic | Coseno sobre embeddings (TF-IDF / local / API) |

## Total

`similarity_total = Σ weight_i * score_i`  
`contributions_i = weight_i * score_i`

## Explicación

Cada resultado incluye símbolos, arquetipos, emociones, keywords compartidos, notas de color y diferencias principales.

## Perfiles

`equilibrado`, `visual`, `psicologico`, `tradicional`, `narrativo` — deben sumar 1.0 (validado).
