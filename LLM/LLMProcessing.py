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

# Use environment variable for API key (set OPENAI_API_KEY)
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "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"))
# Prompt: LLM produces summarized_description + cleaned trip_report_1 and trip_report_2
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
    """Extract latitude/longitude from malformed CSV where coordinates live in headers."""
    coord_pair_re = re.compile(r"^\s*([-+]?\d{1,2}(?:\.\d+)?)\s*,\s*([-+]?\d{1,3}(?:\.\d+)?)\s*$")

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

    # Primary path for this dataset:
    # Coordinates are stored as header names, and each row marks the matching
    # coordinate by containing data in that coordinate column.
    coord_header_hits: list[tuple[str, str]] = []
    for idx, header_value in enumerate(headers):
        if idx >= len(row) or not row[idx].strip():
            continue

        match = coord_pair_re.match(header_value.strip())
        if not match:
            continue

        try:
            lat_val = float(match.group(1))
            lon_val = float(match.group(2))
        except ValueError:
            continue
        if not (-90 <= lat_val <= 90 and -180 <= lon_val <= 180):
            continue

        pair = (str(lat_val), str(lon_val))
        if "map & directions" in row[idx].lower():
            return pair
        coord_header_hits.append(pair)

    if coord_header_hits:
        return coord_header_hits[0]

    coord_text = get_row_value(row, headers, "coordinate", "map & directions", "trailhead gps")

    # Final fallback for any future CSV variants.
    cells_to_scan = [coord_text] if coord_text else []
    cells_to_scan.extend(row)
    for cell in cells_to_scan:
        if not cell:
            continue
        match = re.search(r"([-+]?\d{1,2}(?:\.\d+)?)\s*,\s*([-+]?\d{1,3}(?:\.\d+)?)", cell)
        if not match:
            continue
        try:
            lat_val = float(match.group(1))
            lon_val = float(match.group(2))
        except ValueError:
            continue
        if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
            return (str(lat_val), str(lon_val))

    return (None, None)


def parse_llm_response(response_text: str) -> dict:
    """Extract summarized_description, trip_report_1, trip_report_2 from LLM JSON response."""
    text = response_text.strip()
    # Handle markdown code blocks
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
    trip_id: int | None = None,
) -> dict:
    """
    Build a trip_report_info object per schema.sql.
    trip_id is required for DB insert; pass None to output without it.
    """
    lat, lon = extract_lat_long(row, headers)

    info = {
        "summarized_description": summarized_description,
        "hike_name": get_row_value(row, headers, "hike name"),
        "source_url": get_row_value(row, headers, "url"),
        "distance": get_row_value(row, headers, "length", "length_1"),
        "elevation_gain": get_row_value(row, headers, "elevation gain", "elevation gain_1"),
        "highpoint": get_row_value(row, headers, "highest point", "highest point_1"),
        "difficulty": get_row_value(
            row, headers, "calculated difficulty", "difficulty"
        ),
        "trip_report_1": trip_report_1,
        "trip_report_2": trip_report_2,
        "lat": lat,
        "long": lon,
    }
    if trip_id is not None:
        info["trip_id"] = trip_id
    return info


def get_starting_trip_id() -> int:
    """
    Starting trip_id for trip_report_info-only inserts.
    If TRIP_REPORT_START_TRIP_ID is set, use it; otherwise continue from
    MAX(trip_id)+1 in trip_report_info.
    """
    raw_start = os.environ.get("TRIP_REPORT_START_TRIP_ID")
    if raw_start:
        try:
            start = int(raw_start)
            if start > 0:
                return start
        except ValueError:
            pass

    with get_cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(trip_id), 0) AS max_trip_id FROM trip_report_info")
        row = cur.fetchone()
        max_trip_id = int(row["max_trip_id"]) if row and row.get("max_trip_id") is not None else 0
        return max_trip_id + 1


# Path to CSV (relative to script directory)
script_dir = Path(__file__).parent
csv_file_path = script_dir / "trailData.csv"
next_trip_id = get_starting_trip_id()

with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)

    for row in reader:
        if len(row) < 2:
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
            trip_id=None,
        )

        # Insert into database with a unique trip_id per input row.
        try:
            hike_name = trip_report_info.get("hike_name") or "Unknown Trail"
            trip_id = next_trip_id
            info_id = insert_trip_report_info(trip_id, trip_report_info)
            next_trip_id += 1

            print(f"Inserted trip_report_info id={info_id} for trip id={trip_id} ({hike_name})")
        except RuntimeError as e:
            if "DATABASE_URL" in str(e):
                print("Error: DATABASE_URL not set. Set it to your PostgreSQL connection string.")
            else:
                raise
        except Exception as e:
            print(f"Database error: {e}")
