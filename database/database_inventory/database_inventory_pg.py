from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row

# Predetermined types (match your project enum)
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

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

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

def _split_known_optional_fields(payload: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    known: Dict[str, Any] = {}
    extras = dict(payload)

    for k in ["type", "name", "capacity"]:
        extras.pop(k, None)

    if "weight" in extras:
        known["weight"] = str(extras.pop("weight") or "").strip() or None
    if "brand" in extras:
        known["brand"] = str(extras.pop("brand") or "").strip() or None
    if "condition" in extras:
        known["item_condition"] = str(extras.pop("condition") or "").strip() or None
    if "item_condition" in extras:
        known["item_condition"] = str(extras.pop("item_condition") or "").strip() or None
    if "notes" in extras:
        known["notes"] = str(extras.pop("notes") or "").strip() or None

    cleaned_extras: Dict[str, Any] = {}
    for k, v in extras.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        cleaned_extras[str(k)] = v

    return known, cleaned_extras


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return psycopg.connect(url, row_factory=dict_row)


def ensure_user_exists(username: str) -> dict:
    """
    Create user row if missing (username-only).
    For real auth, you’ll use a proper users table with pw_hash/email;
    but this supports your “username is the key” inventory design.
    """
    username = _normalize_username(username)
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO users (username, email, pw_hash)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
            RETURNING id, username
            """,
            (username, f"{username}@example.com", "placeholder"),
        ).fetchone()
        return row


def add_gear_item(username: str, payload: Dict[str, Any]) -> int:
    user = ensure_user_exists(username)

    gear_type = _normalize_type(payload.get("type"))
    name = _normalize_required_field(payload.get("name"), "name", 1, 50)
    capacity = _normalize_required_field(payload.get("capacity"), "capacity", 1, 50)

    known, extras = _split_known_optional_fields(payload)
    qualities_json = json.dumps(extras, ensure_ascii=False)

    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO gear_items
              (user_id, type, name, capacity, weight, brand, item_condition, notes, qualities_json)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (
                user["id"],
                gear_type,
                name,
                capacity,
                known.get("weight"),
                known.get("brand"),
                known.get("item_condition"),
                known.get("notes"),
                qualities_json,
            ),
        ).fetchone()
        return int(row["id"])


def list_gear(username: str) -> List[Dict[str, Any]]:
    username = _normalize_username(username)

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT gi.*
            FROM gear_items gi
            JOIN users u ON u.id = gi.user_id
            WHERE u.username = %s
            ORDER BY gi.created_at DESC
            """,
            (username,),
        ).fetchall()

    items: List[Dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        item["condition"] = item.pop("item_condition")
        # qualities_json already comes back as dict sometimes; normalize
        q = item.get("qualities_json")
        if isinstance(q, str):
            try:
                item["qualities"] = json.loads(q)
            except json.JSONDecodeError:
                item["qualities"] = {}
        else:
            item["qualities"] = q or {}
        item.pop("qualities_json", None)
        items.append(item)

    return items
