<<<<<<< HEAD
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

from database.database import get_first_user, create_trip, insert_trip_report_info

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
    }
    if trip_id is not None:
        info["trip_id"] = trip_id
    return info


# Path to CSV (relative to script directory)
script_dir = Path(__file__).parent
csv_file_path = script_dir / "trailData.csv"

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

        # Insert into database (first hike only)
        try:
            creator_id = os.environ.get("TRIP_CREATOR_USER_ID")
            if creator_id:
                creator_id = int(creator_id)
            else:
                user = get_first_user()
                if not user:
                    print("Error: No users in database. Create a user first or set TRIP_CREATOR_USER_ID.")
                    break
                creator_id = user["id"]

            hike_name = trip_report_info.get("hike_name") or "Unknown Trail"
            trip_payload = {
                "trip_name": hike_name,
                "trail_name": hike_name,
                "activity_type": "Hiking",
            }
            trip_id = creator_id
            info_id = insert_trip_report_info(trip_id, trip_report_info)

            print(f"Inserted trip_report_info id={info_id} for trip id={trip_id} ({hike_name})")
        except RuntimeError as e:
            if "DATABASE_URL" in str(e):
                print("Error: DATABASE_URL not set. Set it to your PostgreSQL connection string.")
            else:
                raise
        except Exception as e:
            print(f"Database error: {e}")
          # Process first hike only
        break
=======
import openai
import csv

#ADD api key here from discord

# Fixed part of the message
fixed_prompt = "You are a professional hiking guide writer. You are given all data for a specific hike: Hike Name, Trip Report 1 Title & Text, Trip Report 2 Title & Text, Description, Length_1, Highest Point_1, Elevation Gain_1, Calculated Difficulty_1, URL, and Coordinates. Produce a ready-to-publish website page in this format: include a Title & Critical Info section with Hike Name, Distance, Elevation Gain, Highest Point, Difficulty, Trailhead GPS as a clickable Google Maps link, and Permits with links; an Essential Gear section listing appropriate gear (include snow/shoeing gear if relevant, headlamp, trekking poles, rubber boots for huts, water filtration, food, warm layers); a Hike Overview section (~250 words) summarizing the trail using Description, mentioning junctions, scenic views, steep sections, hut amenities, and winter/snow tips; and a Trip Reports section listing each trip report with date and full text, preserving links. Use headings (#, ##), bold key info (distance, elevation, difficulty), make links clickable, and maintain a professional web-friendly style."

# Path to your CSV file
csv_file_path = "trailData.csv"

# Open the CSV file
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    
    # Get headers from the first row
    headers = next(reader)
    
    # Loop through each row
    for row in reader:
        # Combine headers with row values
        row_with_headers = [f"{header}: {value}" for header, value in zip(headers, row)]
        variable_text = " | ".join(row_with_headers)
        
        # Full prompt
        full_prompt = f"{fixed_prompt} {variable_text}"
        
        # Send to OpenAI using the new Chat Completions API
        response = client.responses.create(
            model="gpt-5-mini",  # or "gpt-4" if you have access
            #messages=[
            #    {"role": "system", "content": "You are a helpful assistant."},
            #    {"role": "user", "content": full_prompt}
            #],
            input = full_prompt
            #max_completion_tokens=500
        )
        
        # Extract AI's response
        #ai_text = response.choices[0].message.content.strip()
        
        # Print input and output
        print(f"Input: {variable_text}")
        print(f"Output: {response.output_text}")
        print("-" * 50)
>>>>>>> 0ce3389ba9c07621e415d982c3db12e81a7df70d
