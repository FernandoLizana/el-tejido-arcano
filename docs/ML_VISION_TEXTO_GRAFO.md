# Machine Learning en El Tejido Arcano

## Enfoque

ML **asistivo y explicable**: propone parecidos y pistas. No predice destinos.

## Tres pilares (MVP)

### 1. Visión
- Vector local por carta: histograma HSV, estadísticas de color, energía de bordes, rejilla 4×4.
- PCA + similitud coseno.
- Sin GPU ni descargas pesadas.
- Futuro opcional: CLIP / segmentación de símbolos.

### 2. Texto y significado
- Embeddings sobre el ADN + capas Jodorowsky.
- Proveedor configurable: `tfidf` (default), `local` (sentence-transformers si está instalado), `api`.
- Búsqueda por idea en espacio semántico.

### 3. Grafo y relaciones
- Matriz de afinidad = similitud multidimensional del motor actual.
- Embeddings de nodos vía KernelPCA.
- Vecinos en el espacio de la red + explicación por dimensiones.

## Uso

- UI: menú **Descubrimientos**
- API: `POST /api/ml/recommend`, `POST /api/ml/search`
- Código: `core/ml_lab.py`
- Config: `config/pipeline.yaml` → sección `ml`

## Opcional (mejor texto)

```powershell
.\env\Scripts\python.exe -m pip install sentence-transformers
```

Luego en `pipeline.yaml`:

```yaml
embedding_provider: local
ml:
  text_provider: local
```
