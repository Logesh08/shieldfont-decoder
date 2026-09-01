# ShieldFont Decoder

ShieldFont Decoder is a reverse-engineering tool for **font-based text obfuscation**, where the text stored in a page can differ from what a browser visually renders.

It analyzes the OpenType font itself, reconstructs the substitution mapping, and converts ShieldFont-style obfuscated source text back into normal, copyable Unicode text — **without OCR or browser automation**.

## Live Demo

**[Try ShieldFont Decoder](https://shieldfont-decoder.onrender.com/)**

The bundled `font-ada3.woff2` mapping is pre-generated, so the default decoder starts immediately. The **Advanced** section can analyze another WOFF2, WOFF, TTF, or OTF font at runtime.

## Why this exists

ShieldFont-style protection uses custom font behavior so that automated extraction can see misleading source text while a human looking at the rendered page sees different words or characters.

Rather than trying to recognize the rendered output from pixels, this project treats the font as the source of truth and recovers the transformation directly from its OpenType tables.

## What I reverse engineered

The decoder follows the font data that drives the rendered substitution:

1. Reads the font's `GSUB` table and finds substitutions referenced by the `ccmp` feature.
2. Resolves ligature substitutions, including extension lookups.
3. Takes the resulting ligature glyph and inspects its composite components in the `glyf` table.
4. Maps those component glyphs back to Unicode characters using the font's character map.
5. Extracts single-glyph substitutions as well, which covers transformations such as character or digit permutations.
6. Builds a reusable source-to-rendered mapping and applies it to the obfuscated text.

For word substitutions, decoding uses exact alphabetic token boundaries so the behavior remains aligned with the font's word-level substitution scheme.

## Implementation notes

- **Python + Flask** web application.
- **fontTools** for OpenType parsing.
- Supports **WOFF2, WOFF, TTF, and OTF** uploads.
- Uploaded fonts are identified by a SHA-256-derived ID and their extracted mappings are cached in memory for the server lifetime.
- A pre-generated mapping is bundled for the default ShieldFont font so normal decoding does not require reparsing the font on every request.
- The decoder operates deterministically from font metadata; it does not depend on OCR or image recognition.

## Scope and limitations

This project targets **ShieldFont-style reversible OpenType substitution schemes** where the rendered mapping can be recovered from the font's `GSUB` and `glyf` data.

It is **not** a generic decoder for every custom-font obfuscation technique. Fonts that encode their transformation differently, use non-reconstructable glyph shapes, or do not expose the required substitution/composite information may require a different analysis approach.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000/>.

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

## About ShieldFont

[ShieldFont](https://shieldfont.org/) is an open-source creative technology that uses custom fonts and word substitution to protect written content from automated scraping. Its source project is available on [GitHub](https://github.com/isaqueseneda/shieldfont).

ShieldFont Decoder is an independent research and compatibility tool. It is not affiliated with or endorsed by the ShieldFont project.
