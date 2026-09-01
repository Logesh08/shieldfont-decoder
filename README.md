# ShieldFont Decoder

A small local Python web server that recovers the text visually rendered by
ShieldFont-style OpenType ligature substitution.

The supplied `font-ada3.woff2` mapping is pre-generated, so the default decoder
starts instantly. You can analyze another WOFF2, WOFF, TTF, or OTF file from the
secondary **Advanced** section in the UI.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>.

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

## How it works

The parser reads GSUB ligature substitutions and reconstructs visible text from
the component glyphs stored in the font's `glyf` table. It performs exact word
replacement to preserve the font's word-boundary behavior and also applies
single-character substitutions such as digit permutations.

Uploaded font mappings are cached in memory for the lifetime of the server.
