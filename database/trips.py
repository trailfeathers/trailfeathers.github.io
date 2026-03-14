"""
TrailFeathers - Trip management: CRUD, collaborators, leave_trip, user_has_trip_access; ACTIVITY_TYPES.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor
from .trip_report_info import get_trip_report_info_by_id

# Allowed activity_type values for trips (validated on create/update).
ACTIVITY_TYPES = frozenset({
    "Backpacking",
    "Hiking",
    "Car Camping",
    "Bird Watching",
    "Backcountry Skiing",
    "Mountaineering",
})


def get_trip(trip_id):
    """Return one trip with creator username and trip_report_info_id, or None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, t.trip_report_info_id, u.username AS creator_username, t.created_at, t.notes
               FROM trips t
               JOIN users u ON u.id = t.creator_id
               WHERE t.id = %s""",
            (trip_id,),
        )
        return cur.fetchone()


def create_trip(creator_id, payload):
    """Create a trip and add creator as collaborator. Location must be chosen from catalog (trip_report_info_id). Returns trip id."""
    trip_name = (payload.get("trip_name") or "").strip()
    if not trip_name:
        raise ValueError("Trip name is required")
    activity_type = (payload.get("activity_type") or "").strip()
    if not activity_type or activity_type not in ACTIVITY_TYPES:
        raise ValueError("Activity type must be one of: " + ", ".join(sorted(ACTIVITY_TYPES)))
    intended_start_date = payload.get("intended_start_date")
    if intended_start_date is not None and intended_start_date != "":
        intended_start_date = intended_start_date.strip() or None

    trip_report_info_id = payload.get("trip_report_info_id")
    if trip_report_info_id is None:
        raise ValueError("Please select a location from the catalog.")
    try:
        info_id = int(trip_report_info_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid location selection.")
    location = get_trip_report_info_by_id(info_id)
    if not location:
        raise ValueError("Selected location not found. Please choose from the list.")
    trail_name = (location.get("hike_name") or "").strip() or "Unknown trail"

    notes = (payload.get("notes") or "").strip() if payload.get("notes") is not None else ""

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO trips (creator_id, trip_name, trail_name, activity_type, intended_start_date, trip_report_info_id, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (creator_id, trip_name, trail_name, activity_type, intended_start_date, info_id, notes),
        )
        row = cur.fetchone()
        trip_id = row["id"]
        cur.execute(
            """INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, 'creator')""",
            (trip_id, creator_id),
        )
        return trip_id


def list_trips_for_user(user_id):
    """Return trips where user is creator or in trip_collaborators. Includes creator username and trip_report_info_id."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT t.id, t.trip_name, t.trail_name, t.activity_type, t.intended_start_date,
                      t.creator_id, t.trip_report_info_id, u.username AS creator_username, t.created_at, t.notes
               FROM trips t
               JOIN users u ON u.id = t.creator_id
               WHERE t.creator_id = %s
                  OR EXISTS (SELECT 1 FROM trip_collaborators tc WHERE tc.trip_id = t.id AND tc.user_id = %s)
               ORDER BY t.created_at DESC""",
            (user_id, user_id),
        )
        return cur.fetchall()


def update_trip(trip_id, user_id, payload):
    """Update a trip. Creator may update all fields including notes; collaborators may update only notes."""
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found.")
    notes = (payload.get("notes") or "").strip() if payload.get("notes") is not None else ""

    if trip["creator_id"] != user_id:
        # Collaborator: only allow updating notes
        with get_cursor() as cur:
            cur.execute("""UPDATE trips SET notes = %s WHERE id = %s""", (notes, trip_id))
        return

    # Creator: update all fields
    trip_name = (payload.get("trip_name") or "").strip()
    if not trip_name:
        raise ValueError("Trip name is required")
    activity_type = (payload.get("activity_type") or "").strip()
    if not activity_type or activity_type not in ACTIVITY_TYPES:
        raise ValueError("Activity type must be one of: " + ", ".join(sorted(ACTIVITY_TYPES)))
    intended_start_date = payload.get("intended_start_date")
    if intended_start_date is not None and intended_start_date != "":
        intended_start_date = intended_start_date.strip() or None
    else:
        intended_start_date = None

    trip_report_info_id = payload.get("trip_report_info_id")
    if trip_report_info_id is None:
        raise ValueError("Please select a location from the catalog.")
    try:
        info_id = int(trip_report_info_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid location selection.")
    location = get_trip_report_info_by_id(info_id)
    if not location:
        raise ValueError("Selected location not found. Please choose from the list.")
    trail_name = (location.get("hike_name") or "").strip() or "Unknown trail"

    with get_cursor() as cur:
        cur.execute(
            """UPDATE trips SET trip_name = %s, trail_name = %s, activity_type = %s, intended_start_date = %s, trip_report_info_id = %s, notes = %s
               WHERE id = %s""",
            (trip_name, trail_name, activity_type, intended_start_date, info_id, notes, trip_id),
        )


def delete_trip(trip_id, user_id):
    """Delete a trip. Only the creator may delete. CASCADE removes collaborators, invites, gear."""
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found.")
    if trip["creator_id"] != user_id:
        raise ValueError("Only the trip creator can delete this trip.")
    with get_cursor() as cur:
        cur.execute("DELETE FROM trips WHERE id = %s", (trip_id,))


def leave_trip(trip_id, user_id):
    """Remove the current user from a trip (disband). Only members can leave; creator must delete the trip."""
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found.")
    if trip["creator_id"] == user_id:
        raise ValueError("Trip creator cannot leave; delete the trip instead.")
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM trip_collaborators WHERE trip_id = %s AND user_id = %s",
            (trip_id, user_id),
        )
        if cur.rowcount == 0:
            raise ValueError("You are not a member of this trip.")


def user_has_trip_access(user_id, trip_id):
    """True if user is creator or in trip_collaborators."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT 1 FROM trips t
               WHERE t.id = %s AND t.creator_id = %s
               UNION
               SELECT 1 FROM trip_collaborators tc WHERE tc.trip_id = %s AND tc.user_id = %s""",
            (trip_id, user_id, trip_id, user_id),
        )
        return cur.fetchone() is not None


def list_trip_collaborators(trip_id):
    """Return list of collaborators: id, username, role (includes creator from trip_collaborators)."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.username, tc.role
               FROM trip_collaborators tc
               JOIN users u ON u.id = tc.user_id
               WHERE tc.trip_id = %s
               ORDER BY tc.role = 'creator' DESC, tc.added_at ASC""",
            (trip_id,),
        )
        return cur.fetchall()


def add_trip_collaborator(trip_id, user_id, role="member"):
    """Add a user to trip. Raises ValueError if already a collaborator."""
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM trip_collaborators WHERE trip_id = %s AND user_id = %s", (trip_id, user_id))
        if cur.fetchone():
            raise ValueError("Already a collaborator")
        cur.execute(
            """INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, %s)""",
            (trip_id, user_id, role),
        )


def remove_trip_collaborator(trip_id, user_id, removed_by_user_id):
    """Remove a collaborator from a trip. Only the trip creator may remove; cannot remove the creator.
    Raises ValueError if not creator, trip not found, or target is creator."""
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found.")
    if trip["creator_id"] != removed_by_user_id:
        raise ValueError("Only the trip creator can remove members.")
    if trip["creator_id"] == user_id:
        raise ValueError("Cannot remove the trip creator.")
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM trip_collaborators WHERE trip_id = %s AND user_id = %s",
            (trip_id, user_id),
        )
        if cur.rowcount == 0:
            raise ValueError("User is not a member of this trip.")
