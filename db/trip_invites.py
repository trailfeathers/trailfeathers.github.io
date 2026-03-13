"""Trip invitation management."""
from .connection import get_cursor


def create_trip_invite(trip_id, inviter_id, invitee_id):
    """Create a pending trip invite. Invitee must be a friend; must not already be collaborator or invited. Returns invite id."""
    if inviter_id == invitee_id:
        raise ValueError("Cannot invite yourself")
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM trip_collaborators WHERE trip_id = %s AND user_id = %s", (trip_id, invitee_id))
        if cur.fetchone():
            raise ValueError("Already a member")
        cur.execute(
            "SELECT id, status FROM trip_invites WHERE trip_id = %s AND invitee_id = %s",
            (trip_id, invitee_id),
        )
        existing = cur.fetchone()
        if existing:
            if existing["status"] == "pending":
                raise ValueError("Already invited")
            raise ValueError("Invite was already responded to")
        cur.execute(
            """INSERT INTO trip_invites (trip_id, inviter_id, invitee_id, status)
               VALUES (%s, %s, %s, 'pending') RETURNING id""",
            (trip_id, inviter_id, invitee_id),
        )
        return cur.fetchone()["id"]


def list_trip_invites_pending(trip_id):
    """Return pending invites for this trip: id, invitee_id, invitee_username, inviter_username, created_at."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ti.id, ti.invitee_id, ti.created_at,
                      ue.username AS invitee_username, ui.username AS inviter_username
               FROM trip_invites ti
               JOIN users ue ON ue.id = ti.invitee_id
               JOIN users ui ON ui.id = ti.inviter_id
               WHERE ti.trip_id = %s AND ti.status = 'pending'
               ORDER BY ti.created_at DESC""",
            (trip_id,),
        )
        return cur.fetchall()


def list_incoming_trip_invites(user_id):
    """Return pending trip invites for this user (invitee): id, trip_id, trip_name, inviter_username, created_at."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ti.id, ti.trip_id, ti.created_at,
                      t.trip_name, u.username AS inviter_username
               FROM trip_invites ti
               JOIN trips t ON t.id = ti.trip_id
               JOIN users u ON u.id = ti.inviter_id
               WHERE ti.invitee_id = %s AND ti.status = 'pending'
               ORDER BY ti.created_at DESC""",
            (user_id,),
        )
        return cur.fetchall()


def has_pending_invite_to_trip(user_id, trip_id):
    """True if user has a pending invite to this trip."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM trip_invites WHERE trip_id = %s AND invitee_id = %s AND status = 'pending'",
            (trip_id, user_id),
        )
        return cur.fetchone() is not None


def accept_trip_invite(invite_id, user_id):
    """Invitee accepts: add to trip_collaborators, set invite status accepted. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT trip_id, invitee_id FROM trip_invites WHERE id = %s AND status = 'pending'",
            (invite_id,),
        )
        row = cur.fetchone()
        if not row or row["invitee_id"] != user_id:
            return False
        trip_id = row["trip_id"]
        cur.execute(
            "UPDATE trip_invites SET status = 'accepted' WHERE id = %s",
            (invite_id,),
        )
        cur.execute(
            "INSERT INTO trip_collaborators (trip_id, user_id, role) VALUES (%s, %s, 'member') ON CONFLICT (trip_id, user_id) DO NOTHING",
            (trip_id, user_id),
        )
        return True


def decline_trip_invite(invite_id, user_id):
    """Invitee declines. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE trip_invites SET status = 'declined' WHERE id = %s AND invitee_id = %s AND status = 'pending'",
            (invite_id, user_id),
        )
        return cur.rowcount > 0


def get_trip_id_for_invite(invite_id):
    """Return trip_id for an invite, or None if not found."""
    with get_cursor() as cur:
        cur.execute("SELECT trip_id FROM trip_invites WHERE id = %s", (invite_id,))
        row = cur.fetchone()
        return row["trip_id"] if row else None


def remove_trip_collaborator(trip_id, user_id, removed_by_user_id):
    """Remove a collaborator from a trip. Only the trip creator may remove; cannot remove the creator.
    Raises ValueError if not creator, trip not found, or target is creator."""
    # Import here to avoid circular dependency
    from .trips import get_trip
    
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


def cancel_trip_invite(invite_id, cancelled_by_user_id):
    """Cancel a pending invite. Only the trip creator may cancel. Deletes the invite row.
    Returns True if a row was deleted, False otherwise."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ti.id, ti.trip_id, ti.status
               FROM trip_invites ti
               JOIN trips t ON t.id = ti.trip_id
               WHERE ti.id = %s AND ti.status = 'pending' AND t.creator_id = %s""",
            (invite_id, cancelled_by_user_id),
        )
        row = cur.fetchone()
        if not row:
            return False
        cur.execute("DELETE FROM trip_invites WHERE id = %s", (invite_id,))
        return cur.rowcount > 0


# Helper function for trips module
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


# New function for API convenience
def invite_user_to_trip(trip_id, inviter_id, invitee_username):
    """Create a trip invite by username lookup. Returns invite id. Raises ValueError for issues."""
    # Import here to avoid circular dependency
    from .users import get_user_by_username
    from .friends import list_friends
    from .trips import get_trip, user_has_trip_access
    
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("Trip not found")
    if not user_has_trip_access(inviter_id, trip_id):
        raise ValueError("You must be a member of this trip to invite others")
    invitee = get_user_by_username(invitee_username)
    if not invitee:
        raise ValueError(f"User '{invitee_username}' not found")
    invitee_id = invitee["id"]
    friends = list_friends(inviter_id)
    friend_ids = {f["id"] for f in friends}
    if invitee_id not in friend_ids:
        raise ValueError("You can only invite friends to trips")
    return create_trip_invite(trip_id, inviter_id, invitee_id)
