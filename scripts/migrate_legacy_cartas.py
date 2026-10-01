"""Migra colores desde cartas/ legacy al ADN JSON y opcionalmente a assets."""

from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.color_pipeline import color_features_to_dict, extract_colors  # noqa: E402
from core.utils import load_pipeline_config, setup_logging  # noqa: E402
from schemas.card_schema import CardDNA  # noqa: E402

logger = logging.getLogger("migrate")


def main() -> None:
    setup_logging()
    pipe = load_pipeline_config()
    color_cfg = pipe.get("color", {})
    seed = int(pipe.get("seed", 42))
    cards_dir = ROOT / "data" / "cards"
    legacy = ROOT / "cartas"
    assets = ROOT / "assets" / "cards" / "rws"
    assets.mkdir(parents=True, exist_ok=True)

    for path in sorted(cards_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        card = CardDNA.model_validate(data)
        src = legacy / (card.legacy_filename or Path(card.imagen).name)
        if not src.exists():
            logger.warning("Imagen no encontrada para %s: %s", card.id, src)
            continue
        dest = assets / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
        result = extract_colors(
            src,
            k=int(color_cfg.get("k", 5)),
            seed=seed,
            resize=int(color_cfg.get("resize", 120)),
            border_crop_ratio=float(color_cfg.get("border_crop_ratio", 0.06)),
            exclude_near_white=bool(color_cfg.get("exclude_near_white", True)),
            near_white_threshold=int(color_cfg.get("near_white_threshold", 245)),
            exclude_near_black=bool(color_cfg.get("exclude_near_black", False)),
            near_black_threshold=int(color_cfg.get("near_black_threshold", 12)),
        )
        data["colores"] = color_features_to_dict(result)
        data["imagen"] = f"cartas/{src.name}"
        CardDNA.model_validate(data)  # revalidate
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Migrado color: %s → %s", card.id, data["colores"]["dominantes_hex"][:3])


if __name__ == "__main__":
    main()
