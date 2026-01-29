import os
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

ALLOWED_GEAR_TYPES = {
    "SLEEPING_BAG",
    "SLEEPING_PAD",
    "SHELTER",
    "COOK_SET",
    "BACKPACK",
    "CLOTHING",
    "WATER_TREATMENT",
    "NAVIGATION",
    "FIRST_AID",
    "LUXURY",
    "OTHER"
}

DB_PATH = os.path.join(os.path.dirname(__file__), "trailfeathers.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with _connect() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())


def create_user(username: str) -> Dict[str, Any]:
    username = (username or "").strip()
    if not username:
        raise ValueError("username is required")

    with _connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username) VALUES (?) RETURNING id, username, created_at;",
                (username,),
            )
            row = cur.fetchone()
            return dict(row)
        except sqlite3.IntegrityError:
            # already exists
            cur = conn.execute(
                "SELECT id, username, created_at FROM users WHERE username = ?;",
                (username,),
            )
            row = cur.fetchone()
            return dict(row)


def _validate_required_str(field_name: str, value: Any, min_len: int = 1, max_len: int = 50) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if len(value) < min_len or len(value) > max_len:
        raise ValueError(f"{field_name} must be {min_len}–{max_len} characters")
    return value


def _normalize_attributes(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supports two input styles:
    - explicit payload["attributes"] object
    - extra top-level keys (weight/brand/condition/etc.) get packed into attributes
    """
    reserved = {"username", "type", "name", "capacity", "attributes"}
    attrs: Dict[str, Any] = {}

    if "attributes" in payload and payload["attributes"] is not None:
        if not isinstance(payload["attributes"], dict):
            raise ValueError("attributes must be an object (JSON dictionary)")
        attrs.update(payload["attributes"])

    # Pack any extra top-level keys into attributes
    for k, v in payload.items():
        if k not in reserved:
            attrs[k] = v

    return attrs


def add_gear_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds one gear item to the user's Gear Library.
    Requires an existing user (does not auto-create users).
    """
    username = _validate_required_str("username", payload.get("username"))
    gear_type = _validate_required_str("type", payload.get("type")).upper()
    if gear_type not in ALLOWED_GEAR_TYPES:
        raise ValueError(f"type must be one of: {sorted(ALLOWED_GEAR_TYPES)}")

    name = _validate_required_str("name", payload.get("name"))
    capacity = _validate_required_str("capacity", payload.get("capacity"))

    attributes = _normalize_attributes(payload)
    attributes_json = json.dumps(attributes, ensure_ascii=False) if attributes else None

    with _connect() as conn:
        user_row = conn.execute(
            "SELECT id, username FROM users WHERE username = ?;",
            (username,),
        ).fetchone()
        if not user_row:
            raise ValueError("username does not exist (create user first)")

        cur = conn.execute(
            """
            INSERT INTO gear_items (user_id, type, name, capacity, attributes)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, type, name, capacity, attributes, created_at;
            """,
            (user_row["id"], gear_type, name, capacity, attributes_json),
        )
        row = cur.fetchone()

    result = dict(row)
    result["username"] = username
    result["attributes"] = json.loads(result["attributes"]) if result.get("attributes") else {}
    return result


def get_user_gear(username: str) -> List[Dict[str, Any]]:
    username = _validate_required_str("username", username)
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT gi.id, u.username, gi.type, gi.name, gi.capacity, gi.attributes, gi.created_at
            FROM gear_items gi
            JOIN users u ON u.id = gi.user_id
            WHERE u.username = ?
            ORDER BY gi.created_at DESC;
            """,
            (username,),
        ).fetchall()

    items: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["attributes"] = json.loads(d["attributes"]) if d.get("attributes") else {}
        items.append(d)
    return items


if __name__ == "__main__":
    init_db()
    # quick smoke test
    create_user("dashkim")
    item = add_gear_item({
        "username": "dashkim",
        "type": "SHELTER",
        "name": "2-person tent",
        "capacity": "2-person",
        "weight": "N/A",
        "brand": "Mountain Hardwear",
        "condition": "like new"
    })
    print("Inserted:", item)
    print("All gear:", get_user_gear("dashkim"))
