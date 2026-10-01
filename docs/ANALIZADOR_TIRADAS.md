# Analizador de tiradas

`core/spread_analyzer.py`

## Entrada

Lista de `card_id` (1–N; UI enfatiza 3 cartas).

## Salida (`SpreadAnalyzeResult`)

- metrics: densidad, entropía, resonancia media, carta central
- dominant_patterns / missing_patterns
- bridge_card, strongest_pair, tension_pair
- hidden_paths, narrative_hypotheses
- disclaimer ético

## Camino oculto

`find_hidden_path(card_a, card_b, ...)`  
Modos: `max_similarity`, `narrative`, `archetypal`, `contrast`, `chromatic`.  
Sin ciclos; `max_depth` limitado.

Lenguaje de salida: condicional / hipotético.
