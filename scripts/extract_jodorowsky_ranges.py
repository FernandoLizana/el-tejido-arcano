"""Extrae extractos por arcano (páginas correctas) de La vía del Tarot.

Requiere el PDF local del libro (no incluido). Ruta vía:

  ARCANAGRAPH_JODOROWSKY_PDF  o  argumento CLI
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sources" / "jodorowsky"
OUT.mkdir(parents=True, exist_ok=True)

_DEFAULT_PDF = ROOT / "data" / "sources" / "pdfs" / "la_via_del_tarot.pdf"
PDF = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("ARCANAGRAPH_JODOROWSKY_PDF", str(_DEFAULT_PDF))
)

# Índices PDF 0-based (verificados): título + subtítulo Jodorowsky/Costa
# RWS id <- páginas Marseille del libro
RANGES = {
    "major_00_fool": (74, 76),
    "major_01_magician": (77, 79),
    "major_02_high_priestess": (80, 82),
    "major_03_empress": (83, 85),
    "major_04_emperor": (86, 88),
    "major_05_hierophant": (89, 91),
    "major_06_lovers": (92, 94),
    "major_07_chariot": (95, 97),
    # Marseille VIII Justicia = RWS 11 Justicia
    "major_11_justice": (98, 100),
    "major_09_hermit": (101, 103),
    "major_10_wheel_of_fortune": (104, 106),
    # Marseille XI Fuerza = RWS 08 Fuerza
    "major_08_strength": (107, 109),
    "major_12_hanged_man": (110, 112),
    "major_13_death": (113, 116),
    "major_14_temperance": (117, 119),
    "major_15_devil": (120, 123),
    "major_16_tower": (124, 126),
    "major_17_star": (127, 129),
    "major_18_moon": (130, 132),
    "major_19_sun": (133, 135),
    "major_20_judgement": (136, 138),
    "major_21_world": (139, 141),
}


def main() -> None:
    if not PDF.is_file():
        raise SystemExit(
            f"PDF no encontrado: {PDF}\n"
            "Define ARCANAGRAPH_JODOROWSKY_PDF o pasa la ruta como argumento."
        )
    reader = PdfReader(str(PDF))
    meta = {}
    for cid, (a, b) in RANGES.items():
        parts = []
        for i in range(a, b + 1):
            t = reader.pages[i].extract_text() or ""
            parts.append(t)
        text = "\n\n".join(parts)
        path = OUT / f"{cid}.txt"
        path.write_text(text, encoding="utf-8", errors="replace")
        meta[cid] = {"pages": [a, b], "chars": len(text), "file": path.name}
        print(cid, a, b, len(text))
    (OUT / "ranges.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
