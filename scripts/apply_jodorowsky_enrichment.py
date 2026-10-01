"""Aplica enriquecimiento de La vía del Tarot a data/cards/*.json."""

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
        key = x.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(x.strip())
    return out


def main() -> None:
    enrich_path = ROOT / "data" / "sources" / "jodorowsky" / "enrichment.json"
    payload = json.loads(enrich_path.read_text(encoding="utf-8"))
    source = payload["source"]
    cards_map = payload["cards"]
    fuente_label = f"{source['title']} — {', '.join(source['authors'])}"

    for path in sorted((ROOT / "data" / "cards").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cid = data["id"]
        if cid not in cards_map:
            print("skip", cid)
            continue
        e = cards_map[cid]
        pk = data.setdefault("palabras_clave", {"neutrales": [], "luz": [], "sombra": []})
        pk["luz"] = uniq(list(pk.get("luz") or []) + list(e.get("luz") or []))
        pk["sombra"] = uniq(list(pk.get("sombra") or []) + list(e.get("sombra") or []))
        pk["neutrales"] = uniq(list(pk.get("neutrales") or []) + list(e.get("neutras") or []))
        data["arquetipos"] = uniq(list(data.get("arquetipos") or []) + list(e.get("arquetipos") or []))
        data["emociones"] = uniq(list(data.get("emociones") or []) + list(e.get("emociones") or []))

        significados = [
            s for s in (data.get("significados") or []) if s.get("fuente") != source["title"]
        ]
        significados.append(
            {
                "fuente": source["title"],
                "autores": source["authors"],
                "esencia": e.get("esencia", ""),
                "subtitulo": e.get("subtitulo_libro", ""),
                "en_lectura": e.get("en_lectura", ""),
                "preguntas": e.get("preguntas") or [],
                "palabras_luz": e.get("luz") or [],
                "palabras_sombra": e.get("sombra") or [],
                "palabras_neutrales": e.get("neutras") or [],
            }
        )
        data["significados"] = significados
        data["fuentes"] = uniq(list(data.get("fuentes") or []) + [fuente_label])
        data["version"] = max(int(data.get("version") or 1), 2)
        data["attributions"] = data.get("attributions") or {}
        data["attributions"]["significados_jodorowsky"] = [
            {
                "value": e.get("subtitulo_libro", ""),
                "source": "manual",
                "confidence": 0.85,
                "reviewed": True,
                "author": "laboratorio",
                "method": "parafrasis_estudio_via_del_tarot",
            }
        ]

        CardDNA.model_validate(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("enriched", cid)

    # invalidar cache embeddings (cambia contenido semántico)
    cache = ROOT / "data" / "cache" / "embeddings"
    if cache.exists():
        for f in cache.glob("*.json"):
            f.unlink()
        print("cleared embedding cache")


if __name__ == "__main__":
    main()
