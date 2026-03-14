"""
TrailFeathers - User profiles: display_name, bio, avatar_path, optional avatar upload; used by profile routes.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor, get_db_connection

# Allowed prefix for avatar_path (under static/) — profile duck presets
PROFILE_AVATAR_DIR_PREFIX = "images_for_site/profile_ducks/"


def get_user_profile(user_id):
    """Return profile row for user_id. None if no row.
    Includes avatar_path (static-relative path) and whether an uploaded BYTEA avatar exists."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT user_id, display_name, bio, updated_at,
                      avatar_path,
                      (avatar IS NOT NULL) AS avatar_uploaded,
                      avatar_media_type
               FROM user_profiles WHERE user_id = %s""",
            (user_id,),
        )
        return cur.fetchone()


def upsert_user_profile(user_id, display_name=None, bio=None, avatar_path=None):
    """Insert or update user profile. display_name and bio can be None to clear.
    If avatar_path is str, set preset path and clear uploaded BYTEA avatar.
    If avatar_path is False, clear avatar_path only (keep upload if any)."""
    with get_cursor() as cur:
        if avatar_path is not None and avatar_path is not False:
            # Set path and clear BYTEA so preset takes effect
            cur.execute(
                """INSERT INTO user_profiles (user_id, display_name, bio, avatar_path, avatar, avatar_media_type, updated_at)
                   VALUES (%s, %s, %s, %s, NULL, NULL, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                     display_name = COALESCE(EXCLUDED.display_name, user_profiles.display_name),
                     bio = COALESCE(EXCLUDED.bio, user_profiles.bio),
                     avatar_path = EXCLUDED.avatar_path,
                     avatar = NULL,
                     avatar_media_type = NULL,
                     updated_at = NOW()""",
                (user_id, display_name, bio, avatar_path),
            )
        elif avatar_path is False:
            # Clear preset path only
            cur.execute(
                """INSERT INTO user_profiles (user_id, display_name, bio, updated_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                     display_name = COALESCE(EXCLUDED.display_name, user_profiles.display_name),
                     bio = COALESCE(EXCLUDED.bio, user_profiles.bio),
                     avatar_path = NULL,
                     updated_at = NOW()""",
                (user_id, display_name, bio),
            )
        else:
            cur.execute(
                """INSERT INTO user_profiles (user_id, display_name, bio, updated_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                     display_name = COALESCE(EXCLUDED.display_name, user_profiles.display_name),
                     bio = COALESCE(EXCLUDED.bio, user_profiles.bio),
                     updated_at = NOW()""",
                (user_id, display_name, bio),
            )


def set_profile_avatar_upload(user_id, image_bytes, media_type):
    """Store uploaded avatar bytes; clears avatar_path so upload is shown."""
    if not image_bytes or len(image_bytes) > 2 * 1024 * 1024:
        raise ValueError("Image missing or too large (max 2MB).")
    mt = (media_type or "image/jpeg").strip().lower()
    if mt not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise ValueError("Use JPEG, PNG, GIF, or WebP.")
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO user_profiles (user_id, avatar, avatar_media_type, avatar_path, updated_at)
               VALUES (%s, %s, %s, NULL, NOW())
               ON CONFLICT (user_id) DO UPDATE SET
                 avatar = EXCLUDED.avatar,
                 avatar_media_type = EXCLUDED.avatar_media_type,
                 avatar_path = NULL,
                 updated_at = NOW()""",
            (user_id, image_bytes, mt),
        )


def get_profile_avatar_payload(user_id):
    """Return dict with keys bytes, media_type if user has BYTEA avatar; else None."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT avatar, avatar_media_type FROM user_profiles
               WHERE user_id = %s AND avatar IS NOT NULL""",
            (user_id,),
        )
        row = cur.fetchone()
        if not row or not row.get("avatar"):
            return None
        b = row["avatar"]
        if isinstance(b, memoryview):
            b = b.tobytes()
        return {"bytes": b, "media_type": row.get("avatar_media_type") or "image/jpeg"}


