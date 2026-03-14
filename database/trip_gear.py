"""
Trip gear assignment (trip_gear). get_trip_gear_pool returns all gear from trip
collaborators with is_assigned flag; get_trip_assigned_gear returns only assigned
items. assign_gear_to_trip requires gear owner to be a collaborator; unassign
removes the link. Used by trip dashboard routes.
"""
from .connection import get_cursor


def get_trip_gear_pool(trip_id):
    """Get all gear from trip collaborators that could be assigned to this trip. Includes requirement_type and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.user_id, g.type, g.name, g.capacity, g.weight_oz, 
                      g.brand, g.condition, g.notes, g.requirement_type_id, g.capacity_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name,
                      u.username AS owner_username,
                      CASE WHEN tg.gear_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_assigned
               FROM trip_collaborators tc
               JOIN users u ON u.id = tc.user_id
               JOIN gear g ON g.user_id = tc.user_id
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               LEFT JOIN trip_gear tg ON tg.trip_id = %s AND tg.gear_id = g.id
               WHERE tc.trip_id = %s
               ORDER BY u.username, g.type, g.name""",
            (trip_id, trip_id),
        )
        return cur.fetchall()


def get_trip_assigned_gear(trip_id):
    """Get gear already assigned to this trip with owner info. Includes requirement_type and capacity_persons."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.type, g.name, g.capacity, g.weight_oz, 
                      g.brand, g.condition, g.requirement_type_id, g.capacity_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name,
                      tg.quantity, u.username AS owner_username, tg.assigned_to_user_id
               FROM trip_gear tg
               JOIN gear g ON g.id = tg.gear_id
               LEFT JOIN requirement_types rt ON rt.id = g.requirement_type_id
               JOIN users u ON u.id = g.user_id
               WHERE tg.trip_id = %s
               ORDER BY g.type, g.name""",
            (trip_id,),
        )
        return cur.fetchall()


def assign_gear_to_trip(trip_id, gear_id):
    """Assign a piece of gear to a trip. Owner is determined by gear ownership."""
    with get_cursor() as cur:
        # Verify gear owner is a collaborator
        cur.execute(
            """SELECT g.user_id FROM gear g
               JOIN trip_collaborators tc ON tc.user_id = g.user_id AND tc.trip_id = %s
               WHERE g.id = %s""",
            (trip_id, gear_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Gear not found or owner not in trip")

        owner_id = row["user_id"]
        cur.execute(
            """INSERT INTO trip_gear (trip_id, gear_id, assigned_to_user_id, quantity)
               VALUES (%s, %s, %s, 1)
               ON CONFLICT (trip_id, gear_id) DO NOTHING""",
            (trip_id, gear_id, owner_id),
        )


def unassign_gear_from_trip(trip_id, gear_id):
    """Remove gear assignment from a trip."""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM trip_gear WHERE trip_id = %s AND gear_id = %s",
            (trip_id, gear_id),
        )
