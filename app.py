from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from fontTools.ttLib import TTFont


BASE_DIR = Path(__file__).resolve().parent
MAX_FONT_SIZE = 25 * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FONT_SIZE


def extract_map(font_bytes: bytes) -> dict:
    """Extract ShieldFont's fake-to-visible mappings from OpenType tables."""
    font = TTFont(io.BytesIO(font_bytes), lazy=True)
    if "GSUB" not in font or "glyf" not in font:
        raise ValueError("This font does not contain the required GSUB/glyf tables.")

    glyphs = font["glyf"]
    glyph_to_char = {
        glyph_name: chr(codepoint)
        for codepoint, glyph_name in font.getBestCmap().items()
    }
    words: dict[str, str] = {}
    chars: dict[str, str] = {}

    gsub = font["GSUB"].table
    ccmp_lookups = {
        index
        for feature in gsub.FeatureList.FeatureRecord
        if feature.FeatureTag == "ccmp"
        for index in feature.Feature.LookupListIndex
    }

    for lookup_index, lookup in enumerate(gsub.LookupList.Lookup):
        if lookup_index not in ccmp_lookups:
            continue
        for wrapper in lookup.SubTable:
            lookup_type = lookup.LookupType
            table = wrapper
            if lookup_type == 7:  # Extension substitution
                lookup_type = wrapper.ExtensionLookupType
                table = wrapper.ExtSubTable

            if lookup_type == 4 and hasattr(table, "ligatures"):
                for first, ligatures in table.ligatures.items():
                    for ligature in ligatures:
                        source_names = (first, *ligature.Component)
                        if not all(name in glyph_to_char for name in source_names):
                            continue
                        source = "".join(glyph_to_char[name] for name in source_names)

                        rendered_glyph = glyphs[ligature.LigGlyph]
                        if not rendered_glyph.isComposite():
                            continue
                        component_names = [c.glyphName for c in rendered_glyph.components]
                        if not all(name in glyph_to_char for name in component_names):
                            continue
                        rendered = "".join(glyph_to_char[name] for name in component_names)
                        if source != rendered:
                            words[source] = rendered

            elif lookup_type == 1 and hasattr(table, "mapping"):
                for source_name, rendered_name in table.mapping.items():
                    source = glyph_to_char.get(source_name)
                    rendered = glyph_to_char.get(rendered_name)
                    if source and rendered and source != rendered:
                        chars[source] = rendered

    if not words:
        raise ValueError("No reversible composite ligatures were found in this font.")
    return {"words": words, "chars": chars}


with (BASE_DIR / "default-map.json").open(encoding="utf-8") as file:
    DEFAULT_MAP = json.load(file)

DECODERS = {"default": DEFAULT_MAP}


def decode_text(text: str, mapping: dict) -> tuple[str, int]:
    replacements = 0

    def replace_word(match: re.Match) -> str:
        nonlocal replacements
        original = match.group(0)
        decoded = mapping["words"].get(original, original)
        if decoded != original:
            replacements += 1
        return decoded

    # Exact alphabetic tokens reproduce ShieldFont's word-boundary behaviour.
    decoded = re.sub(r"[A-Za-z]+", replace_word, text)
    char_table = str.maketrans(mapping.get("chars", {}))
    translated = decoded.translate(char_table)
    replacements += sum(a != b for a, b in zip(decoded, translated))
    return translated, replacements


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_words=len(DEFAULT_MAP["words"]),
        default_chars=len(DEFAULT_MAP.get("chars", {})),
    )


@app.post("/api/decode")
def decode():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    font_id = payload.get("fontId", "default")
    if not isinstance(text, str):
        return jsonify(error="Text must be a string."), 400
    mapping = DECODERS.get(font_id)
    if mapping is None:
        return jsonify(error="That uploaded font expired. Upload it again."), 404
    result, replacements = decode_text(text, mapping)
    return jsonify(result=result, replacements=replacements)


@app.post("/api/font")
def upload_font():
    uploaded = request.files.get("font")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose a WOFF2, WOFF, TTF, or OTF file."), 400
    data = uploaded.read()
    if not data:
        return jsonify(error="The selected font is empty."), 400
    font_id = hashlib.sha256(data).hexdigest()[:20]
    try:
        if font_id not in DECODERS:
            DECODERS[font_id] = extract_map(data)
    except Exception as error:
        return jsonify(error=f"Could not decode this font: {error}"), 422
    mapping = DECODERS[font_id]
    return jsonify(
        fontId=font_id,
        name=Path(uploaded.filename).name,
        words=len(mapping["words"]),
        chars=len(mapping.get("chars", {})),
    )


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="Font is too large. Maximum upload size is 25 MB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
