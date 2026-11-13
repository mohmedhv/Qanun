"""Download Journal officiel (JORADP) PDFs listed in the Upgrowth CSV index.

Rules built in:
  * checks the site's robots.txt before every host it contacts (refuses if disallowed)
  * waits --delay seconds between requests (default 3)
  * keeps a registry (data/processed/download_registry.csv) so a second run
    skips files already downloaded -> no duplicates, every file keeps its source URL
  * records whether each PDF has a text layer or is a scan (needs OCR)

Examples (run from the repo root):
  python -m src.collect.downloader --index data/processed/index_jo.csv --issue 1990:17 --issue 2026:57
  python -m src.collect.downloader --index data/processed/index_jo.csv --issue 1990:17 --lang ar
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw_pdf"
REGISTRY = ROOT / "data" / "processed" / "download_registry.csv"
FIELDS = ["url", "file", "year", "number", "lang", "sha256", "bytes",
          "pages", "text_chars_first_pages", "text_status", "downloaded_at"]
URL_RE = re.compile(r"/jo-(francais|arabe)/(\d{4})/[FA](\d{4})(\d{3})\.pdf$", re.I)
USER_AGENT = "QanunStudentProject/0.1 (university course project, polite crawler)"


def read_index(path: Path) -> list[dict]:
    """Return one dict per PDF link found anywhere in the CSV: url, lang, year, number."""
    items = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            for cell in row:
                match = URL_RE.search(cell.strip())
                if match and cell.strip().startswith("http"):
                    items.append({"url": cell.strip(),
                                  "lang": "fr" if match.group(1).lower() == "francais" else "ar",
                                  "year": int(match.group(3)), "number": int(match.group(4))})
    return items


def load_registry() -> dict[str, dict]:
    if not REGISTRY.exists():
        return {}
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        return {row["url"]: row for row in csv.DictReader(handle)}


def save_registry(registry: dict[str, dict]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(registry.values())


def allowed_by_robots(url: str, cache: dict[str, urllib.robotparser.RobotFileParser]) -> bool:
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in cache:
        parser = urllib.robotparser.RobotFileParser(f"{base}/robots.txt")
        parser.read()
        cache[base] = parser
    return cache[base].can_fetch(USER_AGENT, url)


def text_status(path: Path) -> tuple[int, int, str]:
    """(pages, characters in the first 3 pages, 'text' | 'scan' | 'unknown')."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return 0, 0, "unknown"
    with fitz.open(path) as doc:
        chars = sum(len(doc[i].get_text().strip()) for i in range(min(3, len(doc))))
        return len(doc), chars, "text" if chars >= 150 else "scan"


def download(item: dict, registry: dict, robots_cache: dict, delay: float) -> str:
    url = item["url"]
    target = RAW_DIR / url.rsplit("/", 1)[-1]
    if url in registry and target.exists():
        return "skipped (already downloaded)"
    if not allowed_by_robots(url, robots_cache):
        return "REFUSED by robots.txt"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    if response.status_code != 200 or not response.content.startswith(b"%PDF"):
        return f"FAILED (HTTP {response.status_code}, not a PDF?)"
    partial = target.with_suffix(".part")
    partial.write_bytes(response.content)
    partial.replace(target)
    pages, chars, status = text_status(target)
    registry[url] = {"url": url, "file": target.name, "year": item["year"], "number": item["number"],
                     "lang": item["lang"], "sha256": hashlib.sha256(response.content).hexdigest(),
                     "bytes": len(response.content), "pages": pages, "text_chars_first_pages": chars,
                     "text_status": status, "downloaded_at": datetime.now(timezone.utc).isoformat()}
    save_registry(registry)
    time.sleep(delay)
    return f"downloaded ({pages} pages, {status})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", required=True, type=Path, help="Upgrowth CSV file")
    ap.add_argument("--issue", action="append", required=True, metavar="YEAR:NUMBER",
                    help="issue to fetch, e.g. 1990:17 (repeat the option for several)")
    ap.add_argument("--lang", choices=["fr", "ar"], default="fr")
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between requests (>= 3)")
    args = ap.parse_args()
    if args.delay < 3:
        print("Use a delay of at least 3 seconds.")
        return 2

    wanted = {tuple(int(x) for x in issue.split(":")) for issue in args.issue}
    links = [i for i in read_index(args.index) if i["lang"] == args.lang and (i["year"], i["number"]) in wanted]
    missing = wanted - {(i["year"], i["number"]) for i in links}
    for year, number in sorted(missing):
        print(f"{year}:{number} -> not found in the index for lang={args.lang}")
    registry, robots_cache = load_registry(), {}
    for item in links:
        print(f"{item['year']}:{item['number']:03d} {item['url']}\n   {download(item, registry, robots_cache, args.delay)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
