"""
TrailFeathers - Gear Inventory Database

Data format (example POST JSON):
{
  "type": "SLEEP_SYSTEM",
  "name": "2-person tent",
  "capacity": "2P",
  "weight": "N/A",
  "brand": "Mountain Hardwear",
  "condition": "like new",
  "notes": "Freestanding, good in wind"
}
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---- Config ----
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")

# Predetermined gear types (expand anytime, but keep consistent)
GEAR_TYPES = {
    "SLEEP_SYSTEM",
    "SHELTER",
    "BACKPACK",
    "COOKWARE",
    "CLOTHING",
    "WATER",
    "WATER_TREATMENT",
    "NAVIGATION",
    "FIRST_AID",
    "SAFETY",
    "OTHER",
}


# ---- Helpers ----
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enforce foreign keys in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_inventory_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create tables if they don't exist."""
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              username TEXT PRIMARY KEY,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gear_items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL,
              type TEXT NOT NULL,
              name TEXT NOT NULL,
              capacity TEXT NOT NULL,

              -- Common optional fields
              weight TEXT,
              brand TEXT,
              item_condition TEXT,
              notes TEXT,

              -- Flexible optional fields stored as JSON
              qualities_json TEXT NOT NULL DEFAULT '{}',

              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,

              FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_gear_items_username ON gear_items(username);
            CREATE INDEX IF NOT EXISTS idx_gear_items_type ON gear_items(type);
            """
        )


def _normalize_username(username: str) -> str:
    u = (username or "").strip()
    if not u:
        raise ValueError("username is required")
    if len(u) > 50:
        raise ValueError("username must be <= 50 characters")
    return u


def _normalize_required_field(value: Any, field_name: str, min_len: int = 1, max_len: int = 50) -> str:
    v = str(value or "").strip()
    if len(v) < min_len:
        raise ValueError(f"{field_name} is required")
    if len(v) > max_len:
        raise ValueError(f"{field_name} must be {min_len}-{max_len} characters")
    return v


def _normalize_type(value: Any) -> str:
    t = str(value or "").strip().upper()
    if not t:
        raise ValueError("type is required")
    if t not in GEAR_TYPES:
        allowed = ", ".join(sorted(GEAR_TYPES))
        raise ValueError(f"Invalid type '{t}'. Allowed: {allowed}")
    return t


def ensure_user_exists(username: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Idempotent: creates user row if missing."""
    username = _normalize_username(username)
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, created_at) VALUES (?, ?)",
            (username, utc_now_iso()),
        )


def _split_known_optional_fields(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Separate common optional fields we store in dedicated columns
    from extra qualities we store in qualities_json.
    """
    known = {}
    extras = dict(payload)

    for k in ["type", "name", "capacity"]:
        extras.pop(k, None)

    # Common optional fields 
    if "weight" in extras:
        known["weight"] = str(extras.pop("weight") or "").strip() or None
    if "brand" in extras:
        known["brand"] = str(extras.pop("brand") or "").strip() or None
    if "condition" in extras:
        known["item_condition"] = str(extras.pop("condition") or "").strip() or None
    if "item_condition" in extras:
        # allow either key name
        known["item_condition"] = str(extras.pop("item_condition") or "").strip() or None
    if "notes" in extras:
        known["notes"] = str(extras.pop("notes") or "").strip() or None

    # Anything else becomes a flexible quality tag
    # Remove empty values to keep JSON clean.
    cleaned_extras = {}
    for k, v in extras.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        cleaned_extras[str(k)] = v

    return known, cleaned_extras


# crud
def add_gear_item(username: str, payload: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Adds a gear item for a user (auto-creates user row).
    Returns the new gear item id.
    """
    init_inventory_db(db_path)
    username = _normalize_username(username)
    ensure_user_exists(username, db_path=db_path)

    gear_type = _normalize_type(payload.get("type"))
    name = _normalize_required_field(payload.get("name"), "name", 1, 50)
    capacity = _normalize_required_field(payload.get("capacity"), "capacity", 1, 50)

    known, extras = _split_known_optional_fields(payload)
    qualities_json = json.dumps(extras, ensure_ascii=False)

    now = utc_now_iso()

    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO gear_items (
              username, type, name, capacity,
              weight, brand, item_condition, notes,
              qualities_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username, gear_type, name, capacity,
                known.get("weight"), known.get("brand"), known.get("item_condition"), known.get("notes"),
                qualities_json, now, now,
            ),
        )
        return int(cur.lastrowid)


def list_gear(username: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns all gear for a user (most recent first)."""
    init_inventory_db(db_path)
    username = _normalize_username(username)

    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, username, type, name, capacity, weight, brand, item_condition, notes,
                   qualities_json, created_at, updated_at
            FROM gear_items
            WHERE username = ?
            ORDER BY created_at DESC
            """,
            (username,),
        ).fetchall()

    items: List[Dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        # merge flexible qualities into response
        try:
            extras = json.loads(item.pop("qualities_json") or "{}")
        except json.JSONDecodeError:
            extras = {}
        item["qualities"] = extras
        # return as "condition" externally (nicer)
        item["condition"] = item.pop("item_condition")
        items.append(item)

    return items


def get_gear_item(username: str, gear_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    init_inventory_db(db_path)
    username = _normalize_username(username)

    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, username, type, name, capacity, weight, brand, item_condition, notes,
                   qualities_json, created_at, updated_at
            FROM gear_items
            WHERE username = ? AND id = ?
            """,
            (username, int(gear_id)),
        ).fetchone()

    if not row:
        return None

    item = dict(row)
    try:
        extras = json.loads(item.pop("qualities_json") or "{}")
    except json.JSONDecodeError:
        extras = {}
    item["qualities"] = extras
    item["condition"] = item.pop("item_condition")
    return item


def update_gear_item(username: str, gear_id: int, payload: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Partial update. Only updates provided fields.
    Returns True if updated, False if not found.
    """
    init_inventory_db(db_path)
    username = _normalize_username(username)
    gear_id = int(gear_id)

    # Fetch existing first
    existing = get_gear_item(username, gear_id, db_path=db_path)
    if not existing:
        return False

    # Build new values
    new_type = existing["type"]
    if "type" in payload:
        new_type = _normalize_type(payload.get("type"))

    new_name = existing["name"]
    if "name" in payload:
        new_name = _normalize_required_field(payload.get("name"), "name", 1, 50)

    new_capacity = existing["capacity"]
    if "capacity" in payload:
        new_capacity = _normalize_required_field(payload.get("capacity"), "capacity", 1, 50)


    known_updates, extras_updates = _split_known_optional_fields(payload)
    qualities = existing.get("qualities") or {}
    qualities.update(extras_updates)
    qualities_json = json.dumps(qualities, ensure_ascii=False)

    now = utc_now_iso()

    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE gear_items
            SET type = ?,
                name = ?,
                capacity = ?,
                weight = COALESCE(?, weight),
                brand = COALESCE(?, brand),
                item_condition = COALESCE(?, item_condition),
                notes = COALESCE(?, notes),
                qualities_json = ?,
                updated_at = ?
            WHERE username = ? AND id = ?
            """,
            (
                new_type,
                new_name,
                new_capacity,
                known_updates.get("weight"),
                known_updates.get("brand"),
                known_updates.get("item_condition"),
                known_updates.get("notes"),
                qualities_json,
                now,
                username,
                gear_id,
            ),
        )
        return cur.rowcount == 1


def delete_gear_item(username: str, gear_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    init_inventory_db(db_path)
    username = _normalize_username(username)
    gear_id = int(gear_id)

    with _connect(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM gear_items WHERE username = ? AND id = ?",
            (username, gear_id),
        )
        return cur.rowcount == 1


# Test
if __name__ == "__main__":
    init_inventory_db()

    u = "dashkim"
    item_id = add_gear_item(
        u,
        {
            "type": "SHELTER",
            "name": "2-person tent",
            "capacity": "2P",
            "weight": "N/A",
            "brand": "Mountain Hardwear",
            "condition": "like new",
            "season": "3",
            "freestanding": True,
        },
    )
    print("Added gear id:", item_id)
    print("All gear:", list_gear(u))
