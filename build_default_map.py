"""Regenerate default-map.json from the bundled default font."""

import json
from pathlib import Path

from app import extract_map


base = Path(__file__).resolve().parent
font_bytes = (base / "fonts" / "font-ada3.woff2").read_bytes()
mapping = extract_map(font_bytes)

with (base / "default-map.json").open("w", encoding="utf-8") as output:
    json.dump(mapping, output, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

print(
    f"Created {len(mapping['words']):,} word mappings and "
    f"{len(mapping['chars']):,} character mappings."
)
