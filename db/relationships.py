"""Module docstring."""
from .connection import get_cursor, get_db_connection

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


