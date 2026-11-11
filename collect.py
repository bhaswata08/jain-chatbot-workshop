"""Collect public JAIN University web pages into a small Markdown knowledge base.

Usage:
    uv run collect.py                      # reads sources.toml, writes kb/ and jain_kb.zip
    uv run collect.py --out kb --delay 1.5

Each document becomes kb/<category>/<slug>.md with a front-matter header that
records the source URL and fetch time, so the chatbot can cite where an answer
came from. kb/manifest.json lists every document; jain_kb.zip bundles it all
for the lab notebook to download.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from lxml import html as lxml_html

USER_AGENT = "JainKB-StudentWorkshop/1.0 (educational, one-off snapshot)"
MIN_CHARS = 200  # skip pages whose extracted text is shorter than this

# Python's robotparser does prefix matching only, so it cannot evaluate the
# wildcard rules these sites use (e.g. "Disallow: /*.pdf$", "Disallow: /*?").
# Enforce those here as well.
BLOCKED_PATTERNS = [re.compile(r"\.pdf$", re.I), re.compile(r"\?")]


@dataclass
class Doc:
    url: str
    category: str
    title: str
    text: str
    kind: str  # "page" or "text"


class Fetcher:
    def __init__(self, delay: float):
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=30,
        )
        self.delay = delay
        self.robots: dict[str, RobotFileParser] = {}
        self.last_request = 0.0

    def _robots_for(self, url: str) -> RobotFileParser:
        p = urlparse(url)
        root = f"{p.scheme}://{p.netloc}"
        if root not in self.robots:
            rp = RobotFileParser()
            r = self._get_raw(f"{root}/robots.txt")
            rp.parse(r.text.splitlines() if r is not None and r.status_code == 200 else [])
            self.robots[root] = rp
        return self.robots[root]

    def allowed(self, url: str) -> bool:
        if any(p.search(url) for p in BLOCKED_PATTERNS):
            return False
        return self._robots_for(url).can_fetch(USER_AGENT, url)

    def _get_raw(self, url: str) -> httpx.Response | None:
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.last_request = time.monotonic()
        for attempt in range(3):
            try:
                return self.client.get(url)
            except httpx.HTTPError as e:
                print(f"  ! {url}: {e} (attempt {attempt + 1})", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
        return None

    def get(self, url: str) -> httpx.Response | None:
        if not self.allowed(url):
            print(f"  - skip (robots): {url}", file=sys.stderr)
            return None
        r = self._get_raw(url)
        if r is None or r.status_code != 200:
            code = r.status_code if r is not None else "error"
            print(f"  ! {url}: HTTP {code}", file=sys.stderr)
            return None
        return r


# Some public pages list staff by their personal webmail. The KB is published,
# so those addresses are replaced; institutional inboxes are kept.
PERSONAL_EMAIL = re.compile(
    r"[A-Za-z0-9._%+-]+@(?:gmail|googlemail|yahoo|ymail|hotmail|outlook|live|rediffmail|icloud|proton|protonmail)\.[a-z.]{2,6}",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    return PERSONAL_EMAIL.sub("[personal email removed]", text)


def clean(text: str) -> str:
    text = redact(text)
    text = text.replace("\r\n", "\n").replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Page furniture that is never content: site chrome, the "new beta website"
# banner, feedback pop-ups and modals.
DROP_XPATH = (
    "//script | //style | //noscript | //iframe | //svg | //form"
    " | //header | //nav | //footer"
    " | //*[contains(@class, 'beta-banner')] | //*[contains(@class, 'modal')]"
    " | //*[contains(@class, 'feedback')]"
)
BLOCK_TAGS = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "br", "td", "th"}


def strip_chrome(raw: str) -> lxml_html.HtmlElement:
    tree = lxml_html.fromstring(raw)
    for el in tree.xpath(DROP_XPATH):
        el.drop_tree()
    return tree


def full_text(tree: lxml_html.HtmlElement) -> str:
    """All visible text of the page body, one block per line.

    Used for pages such as contact directories, where the useful facts sit in
    small cards that main-content extraction throws away as boilerplate.
    """
    for el in tree.iter():
        if isinstance(el.tag, str) and el.tag in BLOCK_TAGS:
            el.tail = "\n" + (el.tail or "")
    body = tree.find("body")
    text = (body if body is not None else tree).text_content()
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    out: list[str] = []
    for ln in lines:
        if ln and (not out or out[-1] != ln):
            out.append(ln)
    return "\n".join(out)


def collect_page(f: Fetcher, url: str, category: str, mode: str = "main") -> Doc | None:
    r = f.get(url)
    if r is None:
        return None
    meta = trafilatura.extract_metadata(r.text, default_url=url)
    title = (meta.title if meta and meta.title else urlparse(url).path.strip("/")) or url
    tree = strip_chrome(r.text)
    if mode == "full":
        return Doc(url, category, title.strip(), clean(full_text(tree)), "page")
    text = trafilatura.extract(
        lxml_html.tostring(tree, encoding="unicode"),
        url=url,
        output_format="markdown",
        include_tables=True,
        include_links=False,
        include_images=False,
        favor_recall=True,
    )
    return Doc(url, category, title.strip(), clean(text or ""), "page")


def list_text_dir(f: Fetcher, url: str) -> list[str]:
    """Return every .txt URL in an Apache directory listing, recursing into subfolders."""
    r = f.get(url)
    if r is None:
        return []
    found: list[str] = []
    for href in re.findall(r'href="([^"]+)"', r.text):
        if href.startswith(("?", "/", "http")) or href.startswith(".."):
            continue  # sort links, parent dir, absolute links
        full = urljoin(url, href)
        if href.endswith("/"):
            found += list_text_dir(f, full)
        elif href.endswith(".txt"):
            found.append(full)
    return found


def collect_text(f: Fetcher, url: str, category: str) -> Doc | None:
    r = f.get(url)
    if r is None:
        return None
    r.encoding = r.encoding or "utf-8"
    text = clean(r.text)
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    title = first.lstrip("# ").strip()[:120] or Path(urlparse(url).path).stem
    return Doc(url, category, title, text, "text")


def slug_for(url: str) -> str:
    p = urlparse(url)
    host = p.netloc.split(".")[0]  # www, scsit, ...
    path = re.sub(r"\.(txt|php|html?)$", "", p.path.strip("/")) or "home"
    s = re.sub(r"[^a-z0-9]+", "-", f"{host}-{path}".lower()).strip("-")
    return s[:100]


def front_matter(doc: Doc, fetched_at: str) -> str:
    title = doc.title.replace('"', "'")
    return (
        "---\n"
        f'title: "{title}"\n'
        f"source_url: {doc.url}\n"
        f"category: {doc.category}\n"
        f"fetched_at: {fetched_at}\n"
        "---\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", default="sources.toml", type=Path)
    ap.add_argument("--out", default="kb", type=Path)
    ap.add_argument("--zip", default="jain_kb.zip", type=Path)
    ap.add_argument("--delay", default=1.0, type=float, help="seconds between requests")
    args = ap.parse_args()

    cfg = tomllib.loads(args.sources.read_text())
    f = Fetcher(args.delay)
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    targets: list[tuple[str, str, str]] = []  # (url, category, kind)
    for d in cfg.get("text_dir", []):
        print(f"listing {d['url']}")
        targets += [(u, d["category"], "text") for u in list_text_dir(f, d["url"])]
    targets += [(p["url"], p["category"], p.get("extract", "main")) for p in cfg.get("page", [])]

    if args.out.exists():
        for old in args.out.rglob("*.md"):
            old.unlink()
    args.out.mkdir(parents=True, exist_ok=True)

    seen_urls: set[str] = set()
    seen_hashes: dict[str, str] = {}
    manifest = []
    skipped = []
    for i, (url, category, kind) in enumerate(targets, 1):
        if url in seen_urls:
            continue
        seen_urls.add(url)
        print(f"[{i}/{len(targets)}] {url}")
        if kind == "text":
            doc = collect_text(f, url, category)
        else:
            doc = collect_page(f, url, category, mode=kind)
        if doc is None:
            skipped.append({"url": url, "reason": "fetch failed or blocked"})
            continue
        if len(doc.text) < MIN_CHARS:
            skipped.append({"url": url, "reason": f"only {len(doc.text)} chars of text"})
            continue
        h = hashlib.sha256(re.sub(r"\s+", " ", doc.text).encode()).hexdigest()
        if h in seen_hashes:
            skipped.append({"url": url, "reason": f"duplicate of {seen_hashes[h]}"})
            continue
        seen_hashes[h] = url

        rel = Path(category) / f"{slug_for(url)}.md"
        (args.out / rel).parent.mkdir(parents=True, exist_ok=True)
        (args.out / rel).write_text(front_matter(doc, fetched_at) + doc.text + "\n", encoding="utf-8")
        manifest.append(
            {
                "file": rel.as_posix(),
                "title": doc.title,
                "source_url": url,
                "category": category,
                "kind": doc.kind if kind == "text" else f"page:{kind}",
                "chars": len(doc.text),
            }
        )

    (args.out / "manifest.json").write_text(
        json.dumps(
            {"fetched_at": fetched_at, "documents": manifest, "skipped": skipped},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (args.out / "README.md").write_text(
        "# JAIN University knowledge base (unofficial snapshot)\n\n"
        f"Collected from public pages of jainuniversity.ac.in on {fetched_at[:10]} for a student\n"
        "chatbot workshop. It is not an official university dataset and may be out of date.\n"
        "Each file's front matter gives its `source_url`; check there before relying on an answer.\n",
        encoding="utf-8",
    )

    with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(args.out.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(args.out.parent))

    total = sum(d["chars"] for d in manifest)
    print(f"\n{len(manifest)} documents, {total:,} chars -> {args.out}/ and {args.zip}")
    print(f"{len(skipped)} skipped (see {args.out}/manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
