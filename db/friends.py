"""
TrailFeathers - Friends: friend requests, accept/decline, list_friends; used by friends and profile routes.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
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
