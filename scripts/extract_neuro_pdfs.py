"""Extrae frentes y páginas clave de PDFs de neurociencia (paráfrasis/estudio).

Requiere PDFs locales (no incluidos). Rutas vía variables de entorno:

  ARCANAGRAPH_BRAIN_FACTS_PDF
  ARCANAGRAPH_NEURO_PDF2

o argumentos CLI: python scripts/extract_neuro_pdfs.py <pdf1> [pdf2]
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sources" / "neuro"
OUT.mkdir(parents=True, exist_ok=True)

_PDFS_DIR = ROOT / "data" / "sources" / "pdfs"


def _resolve_pdfs() -> list[tuple[Path, str]]:
    if len(sys.argv) > 1:
        return [
            (Path(sys.argv[1]), "brain_facts"),
            *([(Path(sys.argv[2]), "neuro_pdf2")] if len(sys.argv) > 2 else []),
        ]
    return [
        (
            Path(
                os.environ.get(
                    "ARCANAGRAPH_BRAIN_FACTS_PDF",
                    str(_PDFS_DIR / "brain_facts.pdf"),
                )
            ),
            "brain_facts",
        ),
        (
            Path(
                os.environ.get(
                    "ARCANAGRAPH_NEURO_PDF2",
                    str(_PDFS_DIR / "neuro_pdf2.pdf"),
                )
            ),
            "neuro_pdf2",
        ),
    ]


REGION_HINTS = re.compile(
    r"(prefrontal|amygdala|hippocampus|hypothalamus|thalamus|cerebellum|"
    r"cortex|limbic|insula|basal ganglia|brainstem|occipital|temporal|"
    r"parietal|frontal|motor|sensory|dopamine|serotonin|neuron|"
    r"plasticity|memory|emotion|attention|reward|decision|"
    r"prefrontal|amígdala|hipocampo|córtex|corteza|límbico|"
    r"cerebelo|tálamo|hipotálamo)",
    re.I,
)


def extract_front(reader: PdfReader, n: int = 10) -> str:
    parts = []
    for i in range(min(n, len(reader.pages))):
        t = reader.pages[i].extract_text() or ""
        parts.append(f"\n--- page {i + 1} ---\n{t[:3000]}")
    return "\n".join(parts)


def harvest_hits(reader: PdfReader, max_pages: int = 120) -> list[str]:
    hits: list[str] = []
    for i, page in enumerate(reader.pages[:max_pages]):
        t = page.extract_text() or ""
        if not REGION_HINTS.search(t):
            continue
        lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
        kept = []
        for ln in lines:
            if REGION_HINTS.search(ln) or len(kept) and len(kept[-1]) < 80:
                kept.append(ln[:220])
            if len(kept) >= 18:
                break
        if kept:
            hits.append(f"=== page {i + 1} ===\n" + "\n".join(kept[:18]))
    return hits


def main() -> None:
    for pdf, stem in _resolve_pdfs():
        if not pdf.is_file():
            print(f"Omitido (no encontrado): {pdf}")
            continue
        print("Reading", pdf.name, "...")
        reader = PdfReader(str(pdf))
        print("  pages:", len(reader.pages))
        meta = reader.metadata
        title = (meta.title if meta else None) or ""
        author = (meta.author if meta else None) or ""
        (OUT / f"{stem}_meta.txt").write_text(
            f"file={pdf.name}\npages={len(reader.pages)}\ntitle={title}\nauthor={author}\n",
            encoding="utf-8",
        )
        (OUT / f"{stem}_front.txt").write_text(extract_front(reader), encoding="utf-8", errors="replace")
        hits = harvest_hits(reader, max_pages=min(160, len(reader.pages)))
        (OUT / f"{stem}_hits.txt").write_text(
            "\n\n".join(hits[:80]), encoding="utf-8", errors="replace"
        )
        print("  hits pages:", len(hits))


if __name__ == "__main__":
    main()
