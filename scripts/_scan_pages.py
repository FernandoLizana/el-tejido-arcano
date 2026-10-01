from pathlib import Path

text = Path("data/sources/jodorowsky/via_del_tarot_full.txt").read_text(encoding="utf-8")
pages = {}
for block in text.split("===== PAGE ")[1:]:
    num = int(block.split(" =====", 1)[0])
    body = block.split(" =====", 1)[1]
    pages[num] = body

for i in range(64, 155):
    body = pages.get(i, "")
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()][:8]
    if not lines:
        continue
    joined = " / ".join(lines[:5])
    print(f"{i:3d} | {joined[:200]}")
