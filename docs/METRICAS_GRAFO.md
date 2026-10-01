# Métricas de grafo y Tejido Arcano

Implementación: `core/metrics.py`

## Teoría de grafos

grado, grado ponderado, betweenness, closeness, eigenvector, PageRank, clustering, comunidades (Louvain → greedy fallback), modularidad, densidad, distancia media, bridges, nodos centrales/periféricos.

## Métricas propias

| Métrica | Descripción |
|---------|-------------|
| Resonancia | similitud total activa |
| Densidad de tirada | conexiones internas del subset |
| Entropía simbólica | diversidad normalizada 0–1 (no es “malo”) |
| Carta puente | betweenness local + similitud media |
| Elementos ausentes | observación, no veredicto |
| Distancia arquetípica | shortest path con dist=1−sim |
| Tensión interna | ejes altos vs bajos |
| Coherencia narrativa | hipótesis de secuencia de etapas |

Todas se interpretan **dentro del modelo**.
