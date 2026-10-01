"""Aplica enriquecimiento Canseco a data/cards/*.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.card_schema import CardDNA  # noqa: E402


def uniq(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        k = x.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x.strip())
    return out


def main() -> None:
    payload = json.loads(
        (ROOT / "data" / "sources" / "canseco" / "enrichment.json").read_text(encoding="utf-8")
    )
    source = payload["source"]
    cards_map = payload["cards"]
    fuente = f"{source['title']} — {', '.join(source['authors'])}"

    for path in sorted((ROOT / "data" / "cards").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cid = data["id"]
        if cid not in cards_map:
            continue
        e = cards_map[cid]
        pk = data.setdefault("palabras_clave", {"neutrales": [], "luz": [], "sombra": []})
        pk["luz"] = uniq(list(pk.get("luz") or []) + list(e.get("luz") or []))
        pk["sombra"] = uniq(list(pk.get("sombra") or []) + list(e.get("sombra") or []))

        significados = [
            s for s in (data.get("significados") or []) if s.get("fuente") != source["title"]
        ]
        significados.append(
            {
                "fuente": source["title"],
                "autores": source["authors"],
                "esencia": e.get("metafora", ""),
                "subtitulo": "Del dilema a la metáfora",
                "en_lectura": e.get("cinema", ""),
                "preguntas": [e.get("dilema", "")] if e.get("dilema") else [],
                "palabras_luz": e.get("luz") or [],
                "palabras_sombra": e.get("sombra") or [],
                "palabras_neutrales": [],
            }
        )
        data["significados"] = significados
        data["fuentes"] = uniq(list(data.get("fuentes") or []) + [fuente])
        # cinema / metaphor helpers for games
        data["attributions"] = data.get("attributions") or {}
        data["attributions"]["canseco_metafora"] = [
            {
                "value": e.get("metafora", ""),
                "source": "manual",
                "confidence": 0.8,
                "reviewed": True,
                "author": "laboratorio",
                "method": "parafrasis_canseco_dilema_metafora",
            }
        ]
        data["version"] = max(int(data.get("version") or 1), 3)
        CardDNA.model_validate(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("enriched", cid)


if __name__ == "__main__":
    main()
