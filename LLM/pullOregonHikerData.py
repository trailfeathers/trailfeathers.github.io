#!/usr/bin/env python3
"""
pullOregonHikerData.py

Scrapes hike data from the Oregon Hikers Field Guide (oregonhikers.org) and
writes it to oregonHikerData.csv, which can be fed into LLMProcessing.py.

Column names are chosen to match what LLMProcessing.py's find_csv_column()
will detect (case-insensitive substring matching):
  "Hike Name", "URL", "Length", "Elevation Gain", "Highest Point",
  "Difficulty", "Type", "Seasons", "Latitude", "Longitude",
  "Description", "Trip Report 1 Title", "Trip Report 1 Text",
  "Trip Report 2 Title", "Trip Report 2 Text"

Usage:
    # Test with the first hike only (no rate-limiting delay):
    python pullOregonHikerData.py --test

    # Scrape all 150 hikes (rate-limited; ~3+ hours):
    python pullOregonHikerData.py

Rate limiting:
  - 60 seconds between hike page fetches  (HIKE_DELAY_S)
  - 10 seconds between forum page fetches  (FORUM_DELAY_S)
Progress is saved after every hike so the run can be safely interrupted.
"""

import csv
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://www.oregonhikers.org"
LISTING_BASE_URL = (
    "https://www.oregonhikers.org/field_guide/Special:Ask"
    "?q=%5B%5BCategory%3AAll+Season+Hikes%5D%5D"
    "&po=Difficulty%0D%0ADistance%0D%0AElevation+gain"
    "&sort=&order=ASC"
    "&limit=50"
    "&usersearch=yes"
)

SCRIPT_DIR = Path(__file__).parent
OUTPUT_CSV = SCRIPT_DIR / "oregonHikerData.csv"

HIKE_LIMIT   = 150
HIKE_DELAY_S = 60   # seconds between hike page requests
FORUM_DELAY_S = 10  # seconds between forum (trip report) page requests
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; TrailFeathersScraper/1.0; "
        "+https://github.com/trailfeathers)"
    )
}

CSV_FIELDNAMES = [
    "Hike Name",
    "URL",
    "Length",
    "Elevation Gain",
    "Highest Point",
    "Difficulty",
    "Type",
    "Seasons",
    "Latitude",
    "Longitude",
    "Description",
    "Trip Report 1 Title",
    "Trip Report 1 Text",
    "Trip Report 2 Title",
    "Trip Report 2 Text",
]

# Mapping from canonical output key → substrings to search for in infobox row labels
_STAT_ALIASES: dict[str, list[str]] = {
    "Length":         ["distance"],
    "Elevation Gain": ["elevation gain", "elevation"],
    "Highest Point":  ["high point", "highpoint"],
    "Difficulty":     ["difficulty"],
    "Type":           ["type"],
    "Seasons":        ["seasons", "season"],
}


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def fetch(url: str, delay: float = 0) -> BeautifulSoup | None:
    """GET a URL and return a BeautifulSoup object, or None on error."""
    if delay > 0:
        print(f"  Waiting {int(delay)}s before request…")
        time.sleep(delay)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        print(f"  ERROR fetching {url}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Listing page
# ---------------------------------------------------------------------------

def get_hike_urls(limit: int = HIKE_LIMIT) -> list[str]:
    """Fetch the All Season Hikes listing (paginated) and return up to `limit` unique URLs."""
    # Step 1: collect ALL hike URLs from every listing page.
    seen: set[str] = set()
    all_urls: list[str] = []
    offset = 0
    page_size = 50

    EXCLUDE_PREFIXES = ("property:", "special:", "category:", "template:", "help:")
    EXCLUDE_SLUGS = {"main_page", "field_guide"}

    while True:
        page_url = f"{LISTING_BASE_URL}&offset={offset}"
        print(f"Fetching listing page (offset={offset})…")
        soup = fetch(page_url)
        if not soup:
            raise RuntimeError(f"Could not fetch listing page at offset={offset}.")

        results_container = (
            soup.find("div", class_="smw-query-result")
            or soup.find("table", class_="smwtable")
            or soup.find("div", id="query-result")
        )
        search_root = results_container if results_container else soup

        td_links = [a for td in search_root.find_all("td") for a in td.find_all("a", href=True)]
        link_pool = td_links if td_links else search_root.find_all("a", href=True)

        found_on_page = 0
        for a in link_pool:
            href: str = a["href"]
            if "/field_guide/" not in href:
                continue
            slug = href.rstrip("/").rsplit("/", 1)[-1].lower()
            if any(p in href.lower() for p in EXCLUDE_PREFIXES) or slug in EXCLUDE_SLUGS:
                continue
            full_url = urljoin(BASE_URL, href)
            norm = full_url.lower()
            if norm in seen:
                continue
            seen.add(norm)
            all_urls.append(full_url)
            found_on_page += 1

        print(f"  Found {found_on_page} new hike URL(s) on this page ({len(all_urls)} total).")

        if found_on_page == 0:
            break

        offset += page_size

    print(f"Collected {len(all_urls)} total unique hike URLs.")

    # Step 2: evenly sample `limit` hikes across the full alphabetical list
    # so the selection spans A–Z rather than just the first letters.
    total = len(all_urls)
    if total <= limit:
        sampled = all_urls
    else:
        step = total / limit
        sampled = [all_urls[int(i * step)] for i in range(limit)]

    print(f"Sampled {len(sampled)} hikes (1 per every ~{total // limit} in the list).")
    return sampled


# ---------------------------------------------------------------------------
# Forum / trip-report scraper
# ---------------------------------------------------------------------------

def scrape_forum_post(url: str) -> str:
    """
    Fetch a phpBB forum post page and return the text of the first post body.
    Oregon Hikers uses phpBB 3.x; post text is in:
      <div class="content"> inside <div class="postbody">
    Fallback to other common phpBB class names if not found.
    """
    soup = fetch(url, delay=FORUM_DELAY_S)
    if not soup:
        return ""

    # phpBB 3.x – post body wrapper
    postbody = soup.find("div", class_="postbody")
    if postbody:
        content_div = postbody.find("div", class_="content")
        if content_div:
            return content_div.get_text(" ", strip=True)
        return postbody.get_text(" ", strip=True)

    # Generic fallbacks
    for cls in ("post-content", "post-text", "message-text", "content"):
        el = soup.find("div", class_=cls)
        if el:
            return el.get_text(" ", strip=True)

    return ""


# ---------------------------------------------------------------------------
# Hike page scraper
# ---------------------------------------------------------------------------

def _parse_stat_kv(raw_key: str, raw_val: str, stats: dict[str, str]) -> None:
    """Try to match a key/value pair against _STAT_ALIASES and populate stats."""
    raw_key_lower = raw_key.lower()
    for fieldname, aliases in _STAT_ALIASES.items():
        if fieldname in stats:
            continue
        if any(alias in raw_key_lower for alias in aliases):
            stats[fieldname] = raw_val
            break


def _parse_stats(content: BeautifulSoup) -> dict[str, str]:
    """
    Find hike stats in the page content and return a dict keyed by canonical
    CSV fieldname (e.g. "Length", "Difficulty", …).

    Oregon Hikers pages store stats in <ul><li>Key: Value</li>…</ul> lists
    inside the main content area. Falls back to wikitable rows if no list match.
    """
    stats: dict[str, str] = {}

    # Strategy 1: <ul><li> items formatted as "Key: Value"
    for ul in content.find_all("ul"):
        for li in ul.find_all("li"):
            text = li.get_text(" ", strip=True)
            if ":" not in text:
                continue
            raw_key, _, raw_val = text.partition(":")
            raw_key = raw_key.strip()
            raw_val = raw_val.strip()
            if raw_key and raw_val:
                _parse_stat_kv(raw_key, raw_val, stats)
        # Stop early once we have the core fields
        if len(stats) >= 3:
            break

    # Strategy 2: wikitable <tr><th>/<td> rows (original approach)
    if len(stats) < 3:
        for table in content.find_all("table"):
            if not any(kw in table.get_text(" ") for kw in ("Distance", "Difficulty", "Elevation")):
                continue
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) < 2:
                    continue
                raw_key = cells[0].get_text(" ", strip=True).rstrip(":").strip()
                raw_val = cells[1].get_text(" ", strip=True)
                _parse_stat_kv(raw_key, raw_val, stats)
            break

    return stats


def _parse_description(content: BeautifulSoup) -> str:
    """
    Extract the hike description text.
    Strategy: find the "Hike Description" section heading, then collect all
    <p> elements that follow it until the next section heading (<h2>/<h3>).
    Fall back to all <p> elements not inside tables.
    """
    # Try to find a "Hike Description" heading
    desc_heading = None
    for heading in content.find_all(["h2", "h3"]):
        if "hike description" in heading.get_text(strip=True).lower():
            desc_heading = heading
            break

    paragraphs: list[str] = []

    if desc_heading:
        for sibling in desc_heading.next_siblings:
            # Stop at the next section heading
            if hasattr(sibling, "name") and sibling.name in ("h2", "h3"):
                break
            if hasattr(sibling, "name") and sibling.name == "p":
                text = sibling.get_text(" ", strip=True)
                if text and len(text) > 15:
                    paragraphs.append(text)
            elif hasattr(sibling, "find_all"):
                # Also look inside divs that follow the heading
                for p in sibling.find_all("p"):
                    if p.find_parent("table"):
                        continue
                    text = p.get_text(" ", strip=True)
                    if text and len(text) > 15:
                        paragraphs.append(text)
    else:
        # Fallback: all <p> tags not inside tables
        for p in content.find_all("p"):
            if p.find_parent("table"):
                continue
            text = p.get_text(" ", strip=True)
            if text and len(text) > 15:
                paragraphs.append(text)

    return "\n\n".join(paragraphs)


def _parse_gps(content: BeautifulSoup) -> tuple[str, str]:
    """
    Extract GPS coordinates from Hike Finder / map links.
    Oregon Hikers embeds coordinates as ?lat=…&lon=… query parameters.
    Returns (latitude_str, longitude_str) or ("", "").
    """
    for a in content.find_all("a", href=True):
        href: str = a["href"]
        lat_m = re.search(r"lat=([-\d.]+)", href)
        lon_m = re.search(r"lon=([-\d.]+)", href)
        if lat_m and lon_m:
            return lat_m.group(1), lon_m.group(1)
    return "", ""


def _parse_trip_report_links(content: BeautifulSoup) -> list[dict[str, str]]:
    """
    Find links to forum trip report pages (viewtopic.php).
    Returns a list of dicts: {"title": ..., "url": ...}
    """
    seen_urls: set[str] = set()
    reports: list[dict[str, str]] = []

    for a in content.find_all("a", href=True):
        href: str = a["href"]
        if "viewtopic" not in href:
            continue
        full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        reports.append({"title": a.get_text(strip=True), "url": full_url})

    return reports


def scrape_hike_page(url: str) -> dict[str, str]:
    """Scrape one Oregon Hikers field guide page. Returns a flat dict."""
    print(f"  Scraping: {url}")

    result: dict[str, str] = {f: "" for f in CSV_FIELDNAMES}
    result["URL"] = url

    soup = fetch(url)
    if not soup:
        return result

    # Hike name
    h1 = soup.find("h1", id="firstHeading") or soup.find("h1")
    if h1:
        result["Hike Name"] = h1.get_text(strip=True)
    print(f"    Name: {result['Hike Name']}")

    # Main content area
    content = (
        soup.find("div", class_="mw-parser-output")
        or soup.find("div", id="mw-content-text")
    )
    if not content:
        print("    WARNING: could not find main content div; skipping sub-fields.")
        return result

    # Stats / infobox
    stats = _parse_stats(content)
    for field in ("Length", "Elevation Gain", "Highest Point", "Difficulty", "Type", "Seasons"):
        result[field] = stats.get(field, "")

    # Combine distance and route type into the Length field (e.g. "0.8 miles, Out and back")
    # to match the format of other trail data sources.
    if result["Length"] and result["Type"]:
        result["Length"] = f"{result['Length']}, {result['Type']}"
        result["Type"] = ""
    print(
        f"    Dist={result['Length'] or '?'}  "
        f"Elev={result['Elevation Gain'] or '?'}  "
        f"Diff={result['Difficulty'] or '?'}"
    )

    # GPS
    lat, lon = _parse_gps(content)
    result["Latitude"]  = lat
    result["Longitude"] = lon
    if lat:
        print(f"    GPS: {lat}, {lon}")

    # Description
    result["Description"] = _parse_description(content)
    snippet = result["Description"][:80].replace("\n", " ")
    print(f"    Desc: {snippet}{'…' if len(result['Description']) > 80 else ''}")

    # Trip reports
    report_links = _parse_trip_report_links(content)
    print(f"    Found {len(report_links)} trip report link(s).")
    for i, report in enumerate(report_links[:2], start=1):
        result[f"Trip Report {i} Title"] = report["title"]
        text = scrape_forum_post(report["url"])
        result[f"Trip Report {i} Text"] = text
        print(f"    Trip Report {i}: '{report['title']}' ({len(text)} chars)")

    return result


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _load_existing_urls(csv_path: Path) -> set[str]:
    """Return the set of URLs already written to the CSV (for resume support)."""
    if not csv_path.exists():
        return set()
    seen: set[str] = set()
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("URL"):
                    seen.add(row["URL"].strip())
    except Exception:
        pass
    return seen


def _append_hike(csv_path: Path, hike: dict[str, str]) -> None:
    """Append one hike row to the CSV, writing a header if the file is new."""
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(hike)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run scraper: fetch hike URLs (with optional limit), scrape each page with resume, append to OUTPUT_CSV."""
    test_mode = "--test" in sys.argv or os.environ.get("TEST_ONLY") == "1"
    limit = 1 if test_mode else HIKE_LIMIT

    if test_mode:
        print("=== TEST MODE: scraping first hike only (no rate-limit delay) ===")
    else:
        print(
            f"=== Scraping up to {limit} hikes "
            f"({HIKE_DELAY_S}s delay between pages; est. {limit * HIKE_DELAY_S // 60}+ min) ==="
        )

    urls = get_hike_urls(limit=limit)

    # Resume support: skip URLs already in the output CSV
    already_done = _load_existing_urls(OUTPUT_CSV)
    pending = [u for u in urls if u not in already_done]
    skipped = len(urls) - len(pending)
    if skipped:
        print(f"Resuming: skipping {skipped} already-scraped hike(s).")

    for idx, url in enumerate(pending):
        # Rate-limit: wait before every hike except the first in a fresh run.
        if idx > 0 and not test_mode:
            print(f"\n[{idx + 1 + skipped}/{len(urls)}] Rate-limit pause…")
            time.sleep(HIKE_DELAY_S)
        else:
            print(f"\n[{idx + 1 + skipped}/{len(urls)}]")

        try:
            hike = scrape_hike_page(url)
        except Exception as exc:
            print(f"  ERROR scraping {url}: {exc}")
            continue

        _append_hike(OUTPUT_CSV, hike)
        print(f"  Saved → {OUTPUT_CSV.name}")

    total = skipped + len(pending)
    print(f"\nDone. {total} hike(s) in {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
