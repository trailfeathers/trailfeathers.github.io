"""
TrailFeathers - Gear (inventory) management: CRUD, _parse_gear_payload; used by gear and trip_gear routes.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor


def add_gear_item(user_id, payload):
    """Add a gear item for user. Returns new gear id."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Gear name is required")
    gear_type = (payload.get("type") or "other").strip() or "other"
    capacity = (payload.get("capacity") or "").strip() or None
    weight_oz = payload.get("weight_oz")
    if weight_oz is not None and weight_oz != "":
        try:
            weight_oz = float(weight_oz)
        except (TypeError, ValueError):
            weight_oz = None
    else:
        weight_oz = None
    brand = (payload.get("brand") or "").strip() or None
    condition = (payload.get("condition") or "").strip() or None
    notes = (payload.get("notes") or "").strip() or None
    requirement_type_id = payload.get("requirement_type_id")
    if requirement_type_id is not None and requirement_type_id != "":
        try:
            requirement_type_id = int(requirement_type_id)
        except (TypeError, ValueError):
            requirement_type_id = None
    else:
        requirement_type_id = None
    capacity_persons = payload.get("capacity_persons")
    if capacity_persons is not None and capacity_persons != "":
        try:
            capacity_persons = int(capacity_persons)
            if capacity_persons < 1:
                capacity_persons = None
        except (TypeError, ValueError):
            capacity_persons = None
    else:
        capacity_persons = None

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO gear (user_id, type, name, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, gear_type, name, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons),
        )
        row = cur.fetchone()
        return row["id"]


def list_gear(user_id):
    """Return all gear for the given user (by user_id). Includes requirement_type key/display_name and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, g.brand, g.condition, g.notes,
                      g.requirement_type_id, g.capacity_persons, g.created_at,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM gear g
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               WHERE g.user_id = %s ORDER BY g.created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


def get_gear_item(gear_id, user_id):
    """Return one gear item by id if it belongs to user_id, else None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, g.brand, g.condition, g.notes,
                      g.requirement_type_id, g.capacity_persons, g.created_at,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM gear g
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               WHERE g.id = %s AND g.user_id = %s""",
            (gear_id, user_id),
        )
        return cur.fetchone()


def _parse_gear_payload(payload):
    """Parse common gear fields from payload. Returns dict of (name, gear_type, capacity, weight_oz, brand, condition, notes, requirement_type_id, capacity_persons)."""
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("Gear name is required")
    gear_type = (payload.get("type") or "other").strip() or "other"
    capacity = (payload.get("capacity") or "").strip() or None
    weight_oz = payload.get("weight_oz")
    if weight_oz is not None and weight_oz != "":
        try:
            weight_oz = float(weight_oz)
        except (TypeError, ValueError):
            weight_oz = None
    else:
        weight_oz = None
    brand = (payload.get("brand") or "").strip() or None
    condition = (payload.get("condition") or "").strip() or None
    notes = (payload.get("notes") or "").strip() or None
    requirement_type_id = payload.get("requirement_type_id")
    if requirement_type_id is not None and requirement_type_id != "":
        try:
            requirement_type_id = int(requirement_type_id)
        except (TypeError, ValueError):
            requirement_type_id = None
    else:
        requirement_type_id = None
    capacity_persons = payload.get("capacity_persons")
    if capacity_persons is not None and capacity_persons != "":
        try:
            capacity_persons = int(capacity_persons)
            if capacity_persons < 1:
                capacity_persons = None
        except (TypeError, ValueError):
            capacity_persons = None
    else:
        capacity_persons = None
    return {
        "name": name,
        "gear_type": gear_type,
        "capacity": capacity,
        "weight_oz": weight_oz,
        "brand": brand,
        "condition": condition,
        "notes": notes,
        "requirement_type_id": requirement_type_id,
        "capacity_persons": capacity_persons,
    }


def update_gear_item(gear_id, user_id, payload):
    """Update a gear item. Item must belong to user_id. Raises ValueError if not found or validation fails."""
    item = get_gear_item(gear_id, user_id)
    if not item:
        raise ValueError("Gear item not found.")
    parsed = _parse_gear_payload(payload)
    with get_cursor() as cur:
        cur.execute(
            """UPDATE gear SET name = %s, type = %s, capacity = %s, weight_oz = %s, brand = %s, condition = %s, notes = %s, requirement_type_id = %s, capacity_persons = %s
               WHERE id = %s AND user_id = %s""",
            (
                parsed["name"],
                parsed["gear_type"],
                parsed["capacity"],
                parsed["weight_oz"],
                parsed["brand"],
                parsed["condition"],
                parsed["notes"],
                parsed["requirement_type_id"],
                parsed["capacity_persons"],
                gear_id,
                user_id,
            ),
        )


def delete_gear_item(gear_id, user_id):
    """Delete a gear item. Only succeeds if it belongs to user_id. Raises ValueError if not found."""
    item = get_gear_item(gear_id, user_id)
    if not item:
        raise ValueError("Gear item not found.")
    with get_cursor() as cur:
        cur.execute("DELETE FROM gear WHERE id = %s AND user_id = %s", (gear_id, user_id))
