# generate-manga skill

Generate manga images from a topic or URL using the manganize CLI.

## Usage

```
/generate-manga <topic or URL> [--character kurage|gpt] [--output path]
```

## What to do when invoked

1. Check if `manganize` is globally installed:

```bash
which manganize
```

2. If installed globally, run directly:

```bash
manganize topic '<topic>' [--character <name>] [--output <path>]
```

3. If not installed globally, fall back to `uv run` from the repo root:

```bash
uv run manganize topic '<topic>' [--character <name>] [--output <path>]
```

4. Show the user the saved image path when done.

> To install globally (one-time): `uv tool install ./packages/core`

## Examples

```bash
# Topic text
uv run manganize topic 'AIエージェントの仕組み'

# URL (arxiv, blog post, etc.)
uv run manganize topic 'https://arxiv.org/abs/2303.08774'

# Different character
uv run manganize topic 'Rustの所有権システム' --character gpt

# Custom output directory
uv run manganize topic '量子コンピュータ' --output ~/Desktop/manga/
```

## Notes

- Default character: `kurage`
- Available characters: `kurage`, `gpt` (check `characters/` dir for full list)
- Output goes to `output/` in the project root by default
- Requires `GOOGLE_API_KEY` or Vertex AI credentials (see README)
- Generation takes ~1-3 minutes (research → scenario → image)

## Installation (one-time)

To use `manganize` as a global tool:

```bash
cd /path/to/manganize
uv tool install ./packages/core
```
