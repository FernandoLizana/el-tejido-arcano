"""Valida ADN de cartas y taxonomías."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.card_schema import CardDNA  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validate")


def load_taxonomy(name: str) -> set[str]:
    path = ROOT / "data" / "taxonomies" / name
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("items", []))


def main() -> int:
    symbols = load_taxonomy("symbols.json")
    emotions = load_taxonomy("emotions.json")
    archetypes = load_taxonomy("archetypes.json")
    elements = load_taxonomy("elements.json")
    stages = load_taxonomy("narrative_stages.json")

    errors = 0
    warnings = 0
    for path in sorted((ROOT / "data" / "cards").glob("*.json")):
        try:
            card = CardDNA.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.error("INVALID %s: %s", path.name, exc)
            errors += 1
            continue

        for s in card.simbolos:
            if s not in symbols:
                logger.warning("%s simbolo fuera de taxonomia: %s", card.id, s)
                warnings += 1
        for e in card.emociones:
            if e not in emotions:
                logger.warning("%s emocion fuera de taxonomia: %s", card.id, e)
                warnings += 1
        for a in card.arquetipos:
            if a not in archetypes:
                logger.warning("%s arquetipo fuera de taxonomia: %s", card.id, a)
                warnings += 1
        for el in card.elementos:
            if el not in elements:
                logger.warning("%s elemento fuera de taxonomia: %s", card.id, el)
                warnings += 1
        for st in card.etapas_narrativas:
            if st not in stages:
                logger.warning("%s etapa fuera de taxonomia: %s", card.id, st)
                warnings += 1
        logger.info("OK %s", card.id)

    logger.info("Validacion terminada errors=%s warnings=%s", errors, warnings)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
