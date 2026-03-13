import os
import urllib.parse

from flask import Response, jsonify, request

from db import (
    PROFILE_AVATAR_DIR_PREFIX,
    get_profile_avatar_payload,
    get_relationship,
    get_user_by_id,
    get_user_by_username,
    get_user_profile,
    list_top_four_hikes,
    list_user_trip_reports,
    set_profile_avatar_upload,
    upsert_user_profile,
)


def register(app, login):
    # ----------------------
    # Profile API
    # ----------------------
    def _profile_avatar_meta(profile, username):
        """Build avatar fields for JSON: static path and/or upload flag."""
        if not profile:
            return {"avatar_path": None, "avatar_uploaded": False}
        path = profile.get("avatar_path")
        uploaded = bool(profile.get("avatar_uploaded"))
        return {
            "avatar_path": path if path else None,
            "avatar_uploaded": uploaded,
            "avatar_url_upload": (request.url_root.rstrip("/") + "/api/me/avatar") if uploaded else None,
            "avatar_url_public": (
                request.url_root.rstrip("/")
                + "/api/users/"
                + urllib.parse.quote(str(username), safe="")
                + "/avatar"
            )
            if uploaded
            else None,
        }

    def _validate_avatar_path(path):
        """Allow only files under profile_ducks; no path traversal."""
        if not path or not isinstance(path, str):
            return None
        path = path.strip().replace("\\", "/")
        if ".." in path or path.startswith("/"):
            return None
        if not path.startswith(PROFILE_AVATAR_DIR_PREFIX):
            return None
        # remainder should be a single filename
        rest = path[len(PROFILE_AVATAR_DIR_PREFIX) :]
        if not rest or "/" in rest or ".." in rest:
            return None
        static_dir = os.path.normpath(
            os.path.join(app.root_path, "..", "static", PROFILE_AVATAR_DIR_PREFIX)
        )
        full = os.path.normpath(os.path.join(static_dir, rest))
        if not full.startswith(os.path.normpath(static_dir)):
            return None
        if not os.path.isfile(full):
            return None
        return path

    def _public_profile_for_user(target_user_id):
        """Build public profile payload for a user (for profile view page)."""
        target = get_user_by_id(target_user_id)
        if not target:
            return None
        profile = get_user_profile(target_user_id)
        top_four = list_top_four_hikes(target_user_id)
        reports = list_user_trip_reports(target_user_id)
        avatar_path = (profile.get("avatar_path") if profile else None) or None
        avatar_uploaded = bool(profile.get("avatar_uploaded")) if profile else False
        out = {
            "user_id": target["id"],
            "username": target["username"],
            "display_name": (profile.get("display_name") if profile else None) or target["username"],
            "bio": (profile.get("bio") if profile else None) or "",
            "avatar_path": avatar_path,
            "avatar_uploaded": avatar_uploaded,
            "top_four": [
                {
                    "position": r["position"],
                    "trip_report_info_id": r["trip_report_info_id"],
                    "hike_name": r.get("hike_name") or "",
                    "latest_report_id": r.get("latest_report_id"),
                    "image_report_id": r.get("image_report_id"),
                }
                for r in top_four
            ],
            "trip_reports": [
                {
                    "id": r["id"],
                    "title": r.get("title") or "",
                    "hike_name": r.get("hike_name") or "",
                    "date_hiked": r["date_hiked"].isoformat()
                    if hasattr(r.get("date_hiked"), "isoformat")
                    else r.get("date_hiked"),
                    "created_at": r["created_at"].isoformat()
                    if hasattr(r.get("created_at"), "isoformat")
                    else r.get("created_at"),
                }
                for r in reports
            ],
        }
        return out

    @app.get("/api/me/profile")
    def get_my_profile():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        profile = get_user_profile(user["id"])
        out = {"username": user["username"], "display_name": None, "bio": None}
        if profile:
            out["display_name"] = profile.get("display_name")
            out["bio"] = profile.get("bio")
        out.update(_profile_avatar_meta(profile, user["username"]))
        return jsonify(out)

    @app.get("/api/profile-avatars")
    def list_profile_avatars():
        """List preset avatar filenames under static/profile_ducks (public)."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        # static/ is at project root; app.root_path is typically tf_server/
        static_dir = os.path.normpath(
            os.path.join(app.root_path, "..", "static", PROFILE_AVATAR_DIR_PREFIX)
        )
        if not os.path.isdir(static_dir):
            return jsonify(paths=[])
        paths = []
        for name in sorted(os.listdir(static_dir)):
            if name.startswith("."):
                continue
            lower = name.lower()
            if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                paths.append(PROFILE_AVATAR_DIR_PREFIX + name)
        return jsonify(paths=paths)

    @app.put("/api/me/profile")
    def put_my_profile():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        display_name = (payload.get("display_name") or "").strip() or None
        bio = (payload.get("bio") or "").strip() or None
        avatar_path = payload.get("avatar_path")
        if avatar_path is not None:
            if avatar_path == "" or avatar_path is False:
                upsert_user_profile(user["id"], display_name=display_name, bio=bio, avatar_path=False)
            else:
                validated = _validate_avatar_path(avatar_path)
                if not validated:
                    return jsonify(error="Invalid avatar path."), 400
                upsert_user_profile(user["id"], display_name=display_name, bio=bio, avatar_path=validated)
        else:
            upsert_user_profile(user["id"], display_name=display_name, bio=bio)
        profile = get_user_profile(user["id"])
        out = {"username": user["username"], "display_name": None, "bio": None}
        if profile:
            out["display_name"] = profile.get("display_name")
            out["bio"] = profile.get("bio")
        out.update(_profile_avatar_meta(profile, user["username"]))
        return jsonify(out)

    @app.post("/api/me/profile/avatar")
    def post_my_profile_avatar():
        """Upload profile image (multipart file); clears preset path."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if "file" not in request.files:
            return jsonify(error="Missing file."), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify(error="Missing file."), 400
        data = f.read()
        media_type = f.mimetype or "image/jpeg"
        try:
            set_profile_avatar_upload(user["id"], data, media_type)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        profile = get_user_profile(user["id"])
        out = {"ok": True}
        out.update(_profile_avatar_meta(profile, user["username"]))
        return jsonify(out)

    @app.get("/api/users/<path:username>/profile")
    def get_user_profile_route(username):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        target = get_user_by_username(username)
        if not target:
            return jsonify(error="User not found"), 404
        payload = _public_profile_for_user(target["id"])
        if not payload:
            return jsonify(error="User not found"), 404
        return jsonify(payload)

    @app.get("/api/me/avatar")
    def get_my_avatar():
        """Serve uploaded avatar for current user."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = get_profile_avatar_payload(user["id"])
        if not payload:
            return "", 204
        return Response(
            payload["bytes"],
            mimetype=payload["media_type"],
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.get("/api/users/<path:username>/avatar")
    def get_user_avatar(username):
        """Serve uploaded avatar for user by username. No auth so img src from static pages works cross-origin."""
        target = get_user_by_username(username)
        if not target:
            return jsonify(error="User not found"), 404
        payload = get_profile_avatar_payload(target["id"])
        if not payload:
            return "", 204
        return Response(
            payload["bytes"],
            mimetype=payload["media_type"],
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.get("/api/users/<path:username>/relationship")
    def get_user_relationship(username):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        target = get_user_by_username(username)
        if not target:
            return jsonify(error="User not found"), 404
        rel = get_relationship(user["id"], target["id"])
        return jsonify({"status": rel["status"], "request_id": rel.get("request_id")})

