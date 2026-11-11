# Build your own Student Chatbot

Slides and data for a hands-on workshop at the JAIN University School of CS & IT.
You go from "what is an LLM" to a chatbot that answers questions about JAIN and
cites the pages it used.

## Get the files

The [latest release](https://github.com/bhaswata08/jain-chatbot-workshop/releases/latest) has two files:

- `deck.html`: the slides in one file. Download it and open it in any browser, offline.
- `jain_kb.zip`: the JAIN knowledge base the chatbot reads.

To load the knowledge base in a molab (marimo) notebook:

```python
import zipfile
from urllib.request import urlretrieve

urlretrieve(
    "https://github.com/bhaswata08/jain-chatbot-workshop/releases/latest/download/jain_kb.zip",
    "jain_kb.zip",
)
zipfile.ZipFile("jain_kb.zip").extractall(".")  # creates kb/
```

## What is in the repo

| Path | What it is |
| --- | --- |
| `kb/` | The knowledge base: one Markdown file per page, with the source URL in its front matter. `kb/manifest.json` lists every file. |
| `collect.py`, `sources.toml` | The collector that builds `kb/` and `jain_kb.zip` from the pages listed in `sources.toml`. |
| `deck/` | The reveal.js slides. Sources are in `deck/sections/`. |

## About the knowledge base

`kb/` is an unofficial snapshot of public pages on jainuniversity.ac.in. It is
not an official university dataset and may be out of date. Check an answer
against its `source_url` before you rely on it.

The collector obeys each site's `robots.txt`. It also replaces personal webmail
addresses (Gmail, Yahoo and similar) that appear on some pages with
`[personal email removed]`. Official university addresses are kept.

To rebuild it (needs [uv](https://docs.astral.sh/uv/)):

```sh
uv run collect.py
```

## Work on the slides

```sh
cd deck/lib && npm ci && cd ..
node serve.mjs 8765   # live preview at http://localhost:8765
node build.mjs        # writes the single-file deck.html
```
