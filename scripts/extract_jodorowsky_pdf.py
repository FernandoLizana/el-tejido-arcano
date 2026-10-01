"""Extrae texto de La vía del Tarot (Jodorowsky) por arcanos mayores.

Requiere el PDF local del libro (no incluido en el repo). Define la ruta con:

  set ARCANAGRAPH_JODOROWSKY_PDF=ruta/al/libro.pdf
  # o: python scripts/extract_jodorowsky_pdf.py ruta/al/libro.pdf
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "sources" / "jodorowsky"
OUT_DIR.mkdir(parents=True, exist_ok=True)

_DEFAULT_PDF = ROOT / "data" / "sources" / "pdfs" / "la_via_del_tarot.pdf"
PDF = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("ARCANAGRAPH_JODOROWSKY_PDF", str(_DEFAULT_PDF))
)

# Orden Marsella / Jodorowsky (nombres en libro)
# PDF page indices se detectan; fallback por TOC impresa aproximada
CARD_MARKERS = [
    ("major_00_fool", ["Le Mat", "EL LOCO", "El Loco"], "El Loco"),
    ("major_01_magician", ["Le Bateleur", "EL MAGO", "El Mago", "I Le Bateleur"], "El Mago"),
    ("major_02_high_priestess", ["La Papesse", "LA PAPISA", "La Papisa", "II La Papesse"], "La Papisa"),
    ("major_03_empress", ["L'Impératrice", "LA EMPERATRIZ", "La Emperatriz", "III L'Imp"], "La Emperatriz"),
    ("major_04_emperor", ["L'Empereur", "EL EMPERADOR", "El Emperador", "IIII L'Empereur"], "El Emperador"),
    ("major_05_hierophant", ["Le Pape", "EL PAPA", "El Papa", "V Le Pape"], "El Papa"),
    ("major_06_lovers", ["L'Amoureux", "EL ENAMORADO", "El Enamorado", "VI L'Amoureux"], "El Enamorado"),
    ("major_07_chariot", ["Le Chariot", "EL CARRO", "El Carro", "VII Le Chariot"], "El Carro"),
    ("major_08_strength", ["La Force", "LA FUERZA", "La Fuerza", "XI La Force", "VIII La Justice"], "La Justicia/Fuerza"),
    ("major_09_hermit", ["L'Hermite", "EL ERMITA", "El Ermita", "VIIII L'Hermite"], "El Ermitaño"),
    ("major_10_wheel_of_fortune", ["Roue de Fortune", "RUEDA DE FORTUNA", "Rueda de Fortuna"], "La Rueda"),
    ("major_11_justice", ["La Justice", "LA JUSTICIA", "La Justicia", "VIII La Justice", "XI La Force"], "Justicia/Fuerza"),
    ("major_12_hanged_man", ["Le Pendu", "EL COLGADO", "El Colgado", "XII Le Pendu"], "El Colgado"),
    ("major_13_death", ["sans nom", "ARCANO SIN NOMBRE", "Arcano sin nombre", "XIII"], "Arcano XIII"),
    ("major_14_temperance", ["Tempérance", "TEMPLANZA", "Templanza", "XIIII Temp"], "Templanza"),
    ("major_15_devil", ["Le Diable", "EL DIABLO", "El Diablo", "XV Le Diable"], "El Diablo"),
    ("major_16_tower", ["Maison Dieu", "LA TORRE", "La Torre", "XVI La Maison"], "La Torre"),
    ("major_17_star", ["L'Étoile", "LA ESTRELLA", "La Estrella", "XVII L"], "La Estrella"),
    ("major_18_moon", ["La Lune", "LA LUNA", "La Luna", "XVIII La Lune"], "La Luna"),
    ("major_19_sun", ["Le Soleil", "EL SOL", "El Sol", "XVIIII Le Soleil"], "El Sol"),
    ("major_20_judgement", ["Le Jugement", "EL JUICIO", "El Juicio", "XX Le Jugement"], "El Juicio"),
    ("major_21_world", ["Le Monde", "EL MUNDO", "El Mundo", "XXI Le Monde"], "El Mundo"),
]


def fix_text(t: str) -> str:
    # Intentos de reparación de extracción imperfecta
    replacements = {
        "�": "",
        "\u0000": "",
    }
    for a, b in replacements.items():
        t = t.replace(a, b)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def main() -> None:
    if not PDF.is_file():
        raise SystemExit(
            f"PDF no encontrado: {PDF}\n"
            "Define ARCANAGRAPH_JODOROWSKY_PDF o pasa la ruta como argumento."
        )
    reader = PdfReader(str(PDF))
    pages = [(i, fix_text(reader.pages[i].extract_text() or "")) for i in range(len(reader.pages))]

    # Dump full text for offline enrichment
    full_path = OUT_DIR / "via_del_tarot_full.txt"
    full_path.write_text("\n\n".join(f"===== PAGE {i} =====\n{t}" for i, t in pages), encoding="utf-8")
    print("wrote", full_path, "chars", full_path.stat().st_size)

    # Detect chapter starts: line near beginning matching roman + name
    starts: dict[str, int] = {}
    patterns = [
        (r"(?i)^\s*le\s+mat\b", "major_00_fool"),
        (r"(?i)^\s*i\s+le\s+bateleur\b", "major_01_magician"),
        (r"(?i)^\s*ii\s+la\s+papesse\b", "major_02_high_priestess"),
        (r"(?i)^\s*iii\s+l['’]?imp", "major_03_empress"),
        (r"(?i)^\s*iiii\s+l['’]?empereur\b", "major_04_emperor"),
        (r"(?i)^\s*v\s+le\s+pape\b", "major_05_hierophant"),
        (r"(?i)^\s*vi\s+l['’]?amoureux\b", "major_06_lovers"),
        (r"(?i)^\s*vii\s+le\s+chariot\b", "major_07_chariot"),
        (r"(?i)^\s*viii\s+la\s+justice\b", "major_08_justice_marseille"),  # marsella VIII=justicia
        (r"(?i)^\s*viiii\s+l['’]?hermite\b", "major_09_hermit"),
        (r"(?i)^\s*x\s+la\s+roue", "major_10_wheel_of_fortune"),
        (r"(?i)^\s*xi\s+la\s+force\b", "major_11_force_marseille"),  # marsella XI=fuerza
        (r"(?i)^\s*xii\s+le\s+pendu\b", "major_12_hanged_man"),
        (r"(?i)^\s*xiii\b.*sans\s+nom|^\s*xiii\s*$|^\s*arcane\s+sans", "major_13_death"),
        (r"(?i)^\s*xiiii\s+temp", "major_14_temperance"),
        (r"(?i)^\s*xv\s+le\s+diable\b", "major_15_devil"),
        (r"(?i)^\s*xvi\s+la\s+maison", "major_16_tower"),
        (r"(?i)^\s*xvii\s+l['’]?[eé]toile\b", "major_17_star"),
        (r"(?i)^\s*xviii\s+la\s+lune\b", "major_18_moon"),
        (r"(?i)^\s*xviiii\s+le\s+soleil\b", "major_19_sun"),
        (r"(?i)^\s*xx\s+le\s+jugement\b", "major_20_judgement"),
        (r"(?i)^\s*xxi\s+le\s+monde\b", "major_21_world"),
    ]

    for i, text in pages:
        head = "\n".join(text.splitlines()[:12])
        for pat, cid in patterns:
            if re.search(pat, head, re.M):
                if cid not in starts:
                    starts[cid] = i
                    print("start", cid, "page", i)

    # Also scan for Spanish chapter titles alone
    es_patterns = [
        (r"(?i)^\s*el\s+loco\s*$", "major_00_fool"),
        (r"(?i)^\s*el\s+mago\s*$", "major_01_magician"),
        (r"(?i)^\s*la\s+papisa\s*$", "major_02_high_priestess"),
        (r"(?i)^\s*la\s+emperatriz\s*$", "major_03_empress"),
        (r"(?i)^\s*el\s+emperador\s*$", "major_04_emperor"),
        (r"(?i)^\s*el\s+papa\s*$", "major_05_hierophant"),
        (r"(?i)^\s*el\s+enamorado\s*$", "major_06_lovers"),
        (r"(?i)^\s*el\s+carro\s*$", "major_07_chariot"),
        (r"(?i)^\s*la\s+justicia\s*$", "major_08_justice_marseille"),
        (r"(?i)^\s*el\s+ermita", "major_09_hermit"),
        (r"(?i)^\s*la\s+rueda", "major_10_wheel_of_fortune"),
        (r"(?i)^\s*la\s+fuerza\s*$", "major_11_force_marseille"),
        (r"(?i)^\s*el\s+colgado\s*$", "major_12_hanged_man"),
        (r"(?i)^\s*el\s+arcano\s+sin\s+nombre", "major_13_death"),
        (r"(?i)^\s*templanza\s*$", "major_14_temperance"),
        (r"(?i)^\s*el\s+diablo\s*$", "major_15_devil"),
        (r"(?i)^\s*la\s+torre\s*$", "major_16_tower"),
        (r"(?i)^\s*la\s+casa\s+de\s+dios", "major_16_tower"),
        (r"(?i)^\s*la\s+estrella\s*$", "major_17_star"),
        (r"(?i)^\s*la\s+luna\s*$", "major_18_moon"),
        (r"(?i)^\s*el\s+sol\s*$", "major_19_sun"),
        (r"(?i)^\s*el\s+juicio\s*$", "major_20_judgement"),
        (r"(?i)^\s*el\s+mundo\s*$", "major_21_world"),
    ]
    for i, text in pages:
        head = "\n".join(text.splitlines()[:15])
        for pat, cid in es_patterns:
            if re.search(pat, head, re.M) and cid not in starts and i > 40:
                starts[cid] = i
                print("es-start", cid, "page", i)

    (OUT_DIR / "chapter_starts.json").write_text(
        json.dumps(starts, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Map Marseille VIII/XI to our RWS Strength/Justice numbering for extraction chunks
    # In Jodorowsky/Marseille: VIII=Justicia, XI=Fuerza
    # In our RWS data: 08=Fuerza, 11=Justicia
    remap = {
        "major_08_justice_marseille": "major_11_justice",
        "major_11_force_marseille": "major_08_strength",
    }

    ordered = sorted(
        ((remap.get(k, k), v) for k, v in starts.items() if remap.get(k, k).startswith("major_")),
        key=lambda x: x[1],
    )
    # dedupe by card id keeping earliest
    seen = {}
    for cid, pg in ordered:
        if cid not in seen:
            seen[cid] = pg
    ordered = sorted(seen.items(), key=lambda x: x[1])

    excerpts = {}
    for idx, (cid, start) in enumerate(ordered):
        end = ordered[idx + 1][1] if idx + 1 < len(ordered) else min(start + 12, len(pages))
        # Cap chapter length
        end = min(end, start + 14)
        chunk = "\n\n".join(pages[i][1] for i in range(start, end))
        excerpts[cid] = {
            "start_page": start,
            "end_page": end - 1,
            "text": chunk[:12000],
        }
        (OUT_DIR / f"{cid}.txt").write_text(chunk, encoding="utf-8")
        print(cid, start, end - 1, "chars", len(chunk))

    (OUT_DIR / "excerpts.json").write_text(
        json.dumps({k: {"start": v["start_page"], "end": v["end_page"], "chars": len(v["text"])} for k, v in excerpts.items()}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
