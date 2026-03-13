"""Friend requests and relationship helpers."""
from .connection import get_cursor


def create_friend_request(sender_id, receiver_id):
    """Create a pending friend request. Returns request id. Raises ValueError for invalid/duplicate."""
    if sender_id == receiver_id:
        raise ValueError("Cannot send a friend request to yourself")
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, sender_id, receiver_id, status FROM friend_requests
               WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)""",
            (sender_id, receiver_id, receiver_id, sender_id),
        )
        existing = cur.fetchone()
        if existing:
            if existing["status"] == "accepted":
                raise ValueError("Already friends")
            if existing["status"] == "pending":
                if existing["sender_id"] == sender_id:
                    raise ValueError("Request already sent")
                raise ValueError("They already sent you a request")
            raise ValueError("Request already exists")
        cur.execute(
            """INSERT INTO friend_requests (sender_id, receiver_id, status)
               VALUES (%s, %s, 'pending') RETURNING id""",
            (sender_id, receiver_id),
        )
        row = cur.fetchone()
        return row["id"]


def list_incoming_requests(receiver_id):
    """Return pending requests where receiver_id = receiver_id, with sender username."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT fr.id, fr.sender_id, fr.created_at, u.username AS sender_username
               FROM friend_requests fr
               JOIN users u ON u.id = fr.sender_id
               WHERE fr.receiver_id = %s AND fr.status = 'pending'
               ORDER BY fr.created_at DESC""",
            (receiver_id,),
        )
        return cur.fetchall()


def accept_friend_request(request_id, receiver_id):
    """Set request to accepted. Only the receiver can accept. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE friend_requests SET status = 'accepted'
               WHERE id = %s AND receiver_id = %s AND status = 'pending'""",
            (request_id, receiver_id),
        )
        return cur.rowcount > 0


def decline_friend_request(request_id, receiver_id):
    """Set request to declined. Only the receiver can decline. Returns True if updated."""
    with get_cursor() as cur:
        cur.execute(
            """UPDATE friend_requests SET status = 'declined'
               WHERE id = %s AND receiver_id = %s AND status = 'pending'""",
            (request_id, receiver_id),
        )
        return cur.rowcount > 0


def list_friends(user_id):
    """Return list of friends: [{ id, username }] for the other user in each accepted pair."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.username
               FROM friend_requests fr
               JOIN users u ON (u.id = fr.receiver_id AND fr.sender_id = %s)
                          OR (u.id = fr.sender_id AND fr.receiver_id = %s)
               WHERE fr.status = 'accepted'
                 AND (fr.sender_id = %s OR fr.receiver_id = %s)""",
            (user_id, user_id, user_id, user_id),
        )
        return cur.fetchall()


def get_relationship(viewer_id, target_user_id):
    """Return relationship from viewer to target: 'friend' | 'pending_out' | 'pending_in' | 'none'. Optional request_id for pending_in (for accept/decline)."""
    if viewer_id == target_user_id:
        return {"status": "self", "request_id": None}
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, sender_id, receiver_id, status
               FROM friend_requests
               WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)""",
            (viewer_id, target_user_id, target_user_id, viewer_id),
        )
        row = cur.fetchone()
    if not row:
        return {"status": "none", "request_id": None}
    if row["status"] == "accepted":
        return {"status": "friend", "request_id": None}
    if row["sender_id"] == viewer_id:
        return {"status": "pending_out", "request_id": row["id"]}
    return {"status": "pending_in", "request_id": row["id"]}


def remove_friend(viewer_id, target_user_id):
    """Remove friendship (unfriend). Both must be in the accepted pair. Returns True if a row was updated/deleted."""
    if viewer_id == target_user_id:
        return False
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM friend_requests
               WHERE status = 'accepted'
                 AND ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))""",
            (viewer_id, target_user_id, target_user_id, viewer_id),
        )
        return cur.rowcount > 0


def cancel_friend_request(request_id, user_id):
    """Cancel a pending friend request. Only the sender can cancel. Returns True if deleted."""
    with get_cursor() as cur:
        cur.execute(
            """DELETE FROM friend_requests
               WHERE id = %s AND sender_id = %s AND status = 'pending'""",
            (request_id, user_id),
        )
        return cur.rowcount > 0
