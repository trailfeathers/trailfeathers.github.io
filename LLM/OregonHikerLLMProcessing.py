"""
TrailFeathers - Process oregonHikerData.csv with OpenAI; insert into trip_report_info (resumable by source_url).
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from dotenv import load_dotenv
load_dotenv()  # ← THIS MUST COME FIRST

import openai
import csv
import json
import os
import re
import sys
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL")

# Allow importing from project root (database module)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_cursor, insert_trip_report_info

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

fixed_prompt = """
You are a professional hiking guide writer. You are given trail data including: Hike Name, Trip Report 1 Title & Text, Trip Report 2 Title & Text, Description, and other stats.

TASK 1 - Summarized description (~250 words):
Produce a polished hike description for a website. Include key junctions, route-finding notes, scenic views, steep/technical sections, seasonal considerations, snow/winter notes (if relevant), hut/campground amenities (if applicable). Professional, web-friendly tone. Do NOT repeat distance/elevation stats unless contextual.

TASK 2 - Trip reports (clean and prepare for website display):
For each trip report (1 and 2), produce a clean display-ready text block. The raw CSV may have messy formatting, run-on text, or inconsistent structure. For each report:
- Preserve the title and date (extract from the title field if combined)
- Preserve all URLs in plain text format (do NOT convert to clickable markdown or HTML)
- Fix paragraph breaks for readability
- Correct obvious typos and grammar
- Remove redundant boilerplate
- Keep the author's voice and content intact
- Use plain text only
- Do NOT use HTML tags
- Do NOT use markdown formatting
- Use normal paragraphs separated by blank lines

If a trip report is empty or missing, return an empty string for that field.

Respond with ONLY valid JSON in this exact format:
{
  "summarized_description": "your full description text here",
  "trip_report_1": "cleaned plain text trip report 1",
  "trip_report_2": "cleaned plain text trip report 2 (or empty string if none)"
}
"""


def find_csv_column(headers: list[str], *candidates: str) -> str | None:
    """Find first header that contains any of the candidate substrings (case-insensitive)."""
    for h in headers:
        h_lower = h.lower()
        for c in candidates:
            if c.lower() in h_lower:
                return h
    return None


def get_row_value(row: list, headers: list[str], *candidates: str) -> str | None:
    """Get value from row for the first matching header."""
    key = find_csv_column(headers, *candidates)
    if key is None:
        return None
    try:
        idx = headers.index(key)
        val = row[idx].strip() if idx < len(row) else ""
        return val if val else None
    except (ValueError, IndexError):
        return None


def extract_lat_long(row: list, headers: list[str]) -> tuple[str | None, str | None]:
    """Extract latitude and longitude from dedicated Latitude/Longitude columns."""
    raw_lat = get_row_value(row, headers, "latitude", "lat")
    raw_lon = get_row_value(row, headers, "longitude", "long", "lon")
    if raw_lat and raw_lon:
        try:
            lat_val = float(raw_lat)
            lon_val = float(raw_lon)
            if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                return (str(lat_val), str(lon_val))
        except ValueError:
            pass
    return (None, None)


def parse_llm_response(response_text: str) -> dict:
    """Extract summarized_description, trip_report_1, trip_report_2 from LLM JSON response."""
    text = response_text.strip()
    if "```json" in text:
        text = re.sub(r"^.*?```json\s*", "", text, flags=re.DOTALL)
        text = re.sub(r"\s*```.*$", "", text, flags=re.DOTALL)
    elif "```" in text:
        text = re.sub(r"^.*?```\s*", "", text, flags=re.DOTALL)
        text = re.sub(r"\s*```.*$", "", text, flags=re.DOTALL)
    try:
        data = json.loads(text)
        return {
            "summarized_description": (data.get("summarized_description") or "").strip() or response_text,
            "trip_report_1": (data.get("trip_report_1") or "").strip(),
            "trip_report_2": (data.get("trip_report_2") or "").strip(),
        }
    except json.JSONDecodeError:
        return {
            "summarized_description": response_text,
            "trip_report_1": "",
            "trip_report_2": "",
        }


def build_trip_report_info(
    row: list,
    headers: list[str],
    summarized_description: str,
    trip_report_1: str = "",
    trip_report_2: str = "",
) -> dict:
    """Build a trip_report_info object matching schema.sql."""
    lat, lon = extract_lat_long(row, headers)
    return {
        "summarized_description": summarized_description,
        "hike_name": get_row_value(row, headers, "hike name"),
        "source_url": get_row_value(row, headers, "url"),
        "distance": get_row_value(row, headers, "length"),
        "elevation_gain": get_row_value(row, headers, "elevation gain"),
        "highpoint": get_row_value(row, headers, "highest point"),
        "difficulty": get_row_value(row, headers, "difficulty"),
        "trip_report_1": trip_report_1,
        "trip_report_2": trip_report_2,
        "lat": lat,
        "long": lon,
    }


def get_starting_trip_id() -> int:
    """Return MAX(trip_id)+1 from trip_report_info so Oregon hikes append after existing data."""
    with get_cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(trip_id), 0) AS max_trip_id FROM trip_report_info")
        row = cur.fetchone()
        max_trip_id = int(row["max_trip_id"]) if row and row.get("max_trip_id") is not None else 0
        return max_trip_id + 1


def get_already_inserted_urls() -> set[str]:
    """Return source_urls already in trip_report_info to support resume without duplicates."""
    with get_cursor() as cur:
        cur.execute("SELECT source_url FROM trip_report_info WHERE source_url IS NOT NULL")
        return {r["source_url"] for r in cur.fetchall()}


script_dir = Path(__file__).parent
csv_file_path = script_dir / "oregonHikerData.csv"

already_inserted = get_already_inserted_urls()
next_trip_id = get_starting_trip_id()

# For each row: skip if URL already in DB; else call LLM, parse response, insert and add URL to already_inserted.
with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)

    for row in reader:
        if len(row) < 2:
            continue

        source_url = get_row_value(row, headers, "url") or ""
        if source_url and source_url in already_inserted:
            hike_name = get_row_value(row, headers, "hike name") or source_url
            print(f"Skipping already-inserted: {hike_name}")
            continue

        variable_text = " | ".join(
            f"{h}: {v}" for h, v in zip(headers, row) if v.strip()
        )
        full_prompt = f"{fixed_prompt}\n\nTrail data:\n{variable_text}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            print(f"API error: {e}")
            continue

        llm_data = parse_llm_response(response_text)
        trip_report_info = build_trip_report_info(
            row,
            headers,
            summarized_description=llm_data["summarized_description"],
            trip_report_1=llm_data["trip_report_1"],
            trip_report_2=llm_data["trip_report_2"],
        )

        try:
            hike_name = trip_report_info.get("hike_name") or "Unknown Trail"
            trip_id = next_trip_id
            info_id = insert_trip_report_info(trip_id, trip_report_info)
            already_inserted.add(source_url)
            next_trip_id += 1
            print(f"Inserted trip_report_info id={info_id} for trip_id={trip_id} ({hike_name})")
        except RuntimeError as e:
            if "DATABASE_URL" in str(e):
                print("Error: DATABASE_URL not set. Set it to your PostgreSQL connection string.")
            else:
                raise
        except Exception as e:
            print(f"Database error: {e}")