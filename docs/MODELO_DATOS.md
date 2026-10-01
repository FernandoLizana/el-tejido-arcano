# Modelo de datos — ADN simbólico

Cada carta es un JSON validado por `schemas/card_schema.py` (`CardDNA`).

## Campos principales

- Identidad: `id`, `nombre`, `nombre_original`, `numero`, `tipo`, `palo`, `mazo`
- Visual: `imagen`, `colores` (RGB/HEX/LAB, %, luminosidad, saturación, temperatura, histograma)
- Simbólico: `elementos`, `simbolos`, `personajes`, `direcciones`
- Semántico: `palabras_clave` (neutrales/luz/sombra), `arquetipos`, `emociones`, `etapas_narrativas`
- `numerologia`, `fuentes`, `version`, `attributions`, `legacy_filename`

## Taxonomías

`data/taxonomies/*.json` controlan valores preferidos. `scripts/validate_card_data.py` avisa si hay términos fuera de taxonomía.

## Extensión a menores / otros mazos

- `tipo=arcano_menor`, `palo` ∈ {bastos, copas, espadas, oros}
- `mazo` libre (`rider_waite_smith`, `marseille`, …)
- Misma carta en otro mazo → otro `id` o convención `mazo__id`

## Attribution (origen)

```json
{
  "value": "torre",
  "source": "manual",
  "confidence": 1.0,
  "reviewed": true
}
```
