# TrailFeathers

**Purpose:** Project README—overview, core features, code structure, and live site link for the TrailFeathers backpacking trip planner.
**Group:** TrailFeathers
**Authors (alphabetically by last name):** Kim, Smith, Domst, and Snider
**Last updated:** 3/13/26

---

TrailFeathers is a web-based backpacking trip planner designed to help outdoor recreationists organize gear and plan collaborative trips.

**Live site:** [https://trailfeathers.github.io]

## Overview

TrailFeathers allows users to:

- Digitally store and manage personal gear inventories
- Create and save trip plans
- Add collaborators to trips
- Generate AI-powered summaries of trip reports and location conditions

The system is built around a relational database (PostgreSQL) and integrates AI-generated summaries to provide relevant planning insights.

---

## Core Features

### Gear Inventory
Users can:
- Add, edit, and manage personal gear items
- Categorize gear (e.g., Sleep System, Cookware, Bag)
- Store optional gear attributes (weight, brand, condition)

### Trip Creation
Users can:
- Create trips with a trail name and activity type
- Set intended start dates
- Add collaborators
- Save trips for later planning

### AI Summary
For each saved trip, the system:
- Retrieves the trail name from the database
- Gathers relevant trip report information
- Generates a summarized overview for the user

---

## Code Structure

- **`app.py`** — WSGI entry point; creates the Flask app via `tf_server.create_app()` (e.g. for Gunicorn).

- **`auth/`** — Session-based authentication. `login.py` defines signup, login, logout, and current-user logic; uses the database for users and caches gear, friends, and trips in the session. Routes are registered in `tf_server/factory.py` as `/api/signup`, `/api/login`, `/api/logout`, `/api/me`.

- **`tf_server/`** — Flask application factory and API routes. `factory.py` builds the app, configures CORS and session cookies, and registers auth and feature routes. `routes/` contains per-feature modules (e.g. `gear.py`, `friends.py`, `profile.py`, `trips.py`, `trip_reports.py`, `wishlist.py`, `locations.py`, `top_four.py`, `health.py`, `options.py`) that expose REST-style endpoints and use the database and auth helpers.

- **`database/`** — Data access layer for PostgreSQL. `connection.py` provides `get_cursor()` and `get_db_connection()`. `database.py` re-exports the public API; domain logic lives in submodules such as `users.py`, `trip_report_info.py`, `gear.py`, `friends.py`, `trips.py`, `trip_invites.py`, `trip_gear.py`, `profiles.py`, `user_trip_reports.py`, `top_four.py`, `favorites.py`, `wishlist.py`, `requirements.py`. Migrations live in `database/migrations/`.

- **`static/`** — Frontend assets: HTML pages (e.g. `login.html`, `dashboard.html`, `inventory.html`, `trip_dashboard.html`), `css/` (main.css plus per-page styles), `js/` (config, utils, auth, navigation, and page-specific scripts). The social center (friends, profiles, trip reports) is under `static/social_center/`. Images (banners, profile ducks, weather icons) are in `static/images_for_site/`.

- **`LLM/`** — Scripts for ingesting and processing trail data: scrapers (`pullTrailData.py`, `pullOregonHikerData.py`) produce CSVs; `LLMProcessing.py` and `OregonHikerLLMProcessing.py` use OpenAI to summarize and insert rows into `trip_report_info`. Intended for one-off or manual runs; rely on `OPENAI_API_KEY` and `DATABASE_URL`.

- **`scripts/`** — Utility scripts (e.g. image splitting for weather/profile assets).

- **`documents/`** — Project docs (PRD, SRS, design diagrams).


