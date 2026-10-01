# Roadmap

## Hecho (iteración 1)

Auditoría, ADN 22 mayores, cromático LAB/ΔE, motor multidimension, grafo multicapa top-k, métricas, tiradas 3, camino oculto, API, UI, tests, docs.

## Hecho (experiencias)

- Modo historia (3 cartas + finales alternativos)
- Constelación enfocada con explicación
- Juego del puente
- Exportar lámina PNG
- Carta del día en Inicio
- ML visión / texto / grafo (Descubrimientos)

## Hecho (cartas + fuentes + juegos)

- Enriquecimiento dual: Jodorowsky (*La vía del Tarot*) + Canseco (*El tarot: del dilema a la metáfora*)
- **Juegos de cartas:** Memoria arcana, ¿Cuál no encaja?, Oráculo de 1 minuto, Tirada-cine
- Detalle de carta con ambas voces de estudio

## Hecho (mapa neurológico)

- Fuentes: *Brain Facts* (SfN 2018) + Drubach et al. (imaginación)
- 15 regiones esquemáticas + mapeo de 22 mayores
- Vista 3D Plotly (landmarks) y sección **Mapa neurológico** en Streamlit
- Disclaimer educativo (no clínico)

## Hecho (Quién eres)

- Test arcano estilo aventura: preguntas de opción múltiple que suman afinidad simbólica con los 22 mayores, sin diagnóstico psicológico.
- Carta guía por fecha: suma de dígitos de AAAAMMDD y reducción módulo 22 (El Loco = 0).
- Mapa personal de 22 cartas: permutación determinista con SHA-256 desde fecha de nacimiento y, opcionalmente, la carta del test como modificador.
- UI en Streamlit con lenguaje reflexivo, educativo y no predictivo.

## Próximo

- Arcanos menores + editor ADN
- sentence-transformers opcional empaquetado
- Comparador Rider–Marsella con datos reales
- SQLite completo para tiradas personales
- Persistencia de settings YAML vía API
- Presets visuales avanzados
- Leiden / MST views
- Mejoras de máscara de fondo en color
- Animaciones más ricas en la constelación
- Compartir tirada por enlace
