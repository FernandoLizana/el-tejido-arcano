"""Extrae páginas de estudio de El tarot (Canseco).

Requiere el PDF local del libro (no incluido). Ruta vía:

  ARCANAGRAPH_CANSECO_PDF  o  argumento CLI
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sources" / "canseco"
OUT.mkdir(parents=True, exist_ok=True)

_DEFAULT_PDF = ROOT / "data" / "sources" / "pdfs" / "el_tarot_canseco.pdf"
PDF = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("ARCANAGRAPH_CANSECO_PDF", str(_DEFAULT_PDF))
)

if not PDF.is_file():
    raise SystemExit(
        f"PDF no encontrado: {PDF}\n"
        "Define ARCANAGRAPH_CANSECO_PDF o pasa la ruta como argumento."
    )

reader = PdfReader(str(PDF))
parts = []
for i in range(65, 91):
    t = reader.pages[i].extract_text() or ""
    parts.append(f"===== PAGE {i} =====\n{t}")
text = "\n\n".join(parts)
(OUT / "majors_extract.txt").write_text(text, encoding="utf-8", errors="replace")
print("chars", len(text))
print(text[:3000])
