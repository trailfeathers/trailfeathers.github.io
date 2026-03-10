import json
import os
import urllib.request
import urllib.parse
from datetime import date, datetime, timedelta

from flask import Flask, request, jsonify, session, Response
from flask_cors import CORS

# Import auth routes (this file defines routes on an app instance)
from auth import login

# Import gear, friend, and trip DB helpers
from database.database import (
    add_gear_item,
    list_gear,
    get_gear_item,
    update_gear_item,
    delete_gear_item,
    get_user_by_id,
    get_user_by_username,
    create_friend_request,
    list_incoming_requests,
    accept_friend_request,
    decline_friend_request,
    list_friends,
    remove_friend,
    cancel_friend_request,
    list_favorite_hikes,
    add_favorite_hike,
    remove_favorite_hike,
    get_user_profile,
    upsert_user_profile,
    set_profile_avatar_upload,
    get_profile_avatar_payload,
    PROFILE_AVATAR_DIR_PREFIX,
    list_top_four_hikes,
    list_top_four_eligible_hikes,
    replace_top_four,
    list_user_trip_reports,
    get_user_trip_report,
    create_user_trip_report,
    update_user_trip_report,
    delete_user_trip_report,
    set_trip_report_image_upload,
    get_trip_report_image_payload,
    list_wishlist,
    add_wishlist_item,
    remove_wishlist_item,
    get_relationship,
    create_trip,
    update_trip,
    delete_trip,
    leave_trip,
    list_trips_for_user,
    get_trip,
    user_has_trip_access,
    has_pending_invite_to_trip,
    list_trip_collaborators,
    add_trip_collaborator,
    create_trip_invite,
    list_trip_invites_pending,
    list_incoming_trip_invites,
    accept_trip_invite,
    decline_trip_invite,
    get_trip_id_for_invite,
    remove_trip_collaborator,
    cancel_trip_invite,
    list_requirement_types,
    get_trip_requirement_summary,
    get_trip_gear_pool,
    get_trip_assigned_gear,
    assign_gear_to_trip,
    unassign_gear_from_trip,
    list_trip_report_info_for_selection,
    get_trip_report_info_for_trip,
)

def create_app():
    app = Flask(__name__)

    # ----------------------
    # Config
    # ----------------------
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "dev-insecure-secret-key-change-me"
    )

    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    # SameSite=None so cookie is sent on cross-origin requests (GitHub Pages → Render); requires Secure
    app.config["SESSION_COOKIE_SAMESITE"] = "None" if os.getenv("RENDER") else "Lax"
    app.config["SESSION_COOKIE_SECURE"] = bool(os.getenv("RENDER"))

    # ----------------------
    # CORS (sessions!)
    # ----------------------
    origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)
    if "https://trailfeathers.github.io" not in origins:
        origins.append("https://trailfeathers.github.io")

    CORS(
        app,
        supports_credentials=True,
        origins=origins,
    )

    # Preflight OPTIONS must return 2xx for CORS
    @app.route("/api/signup", methods=["OPTIONS"])
    @app.route("/api/login", methods=["OPTIONS"])
    @app.route("/api/gear", methods=["OPTIONS"])
    @app.route("/api/gear/<int:gear_id>", methods=["OPTIONS"])
    @app.route("/api/friends/request", methods=["OPTIONS"])
    @app.route("/api/friends/requests", methods=["OPTIONS"])
    @app.route("/api/friends", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/accept", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/checklist", methods=["OPTIONS"])
    @app.route("/api/requirement-types", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/collaborators", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/collaborators/<int:user_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/accept", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/pool", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/<int:gear_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/dashboard", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/weather", methods=["OPTIONS"])
    @app.route("/api/locations", methods=["OPTIONS"])
    @app.route("/api/me/favorites", methods=["OPTIONS"])
    @app.route("/api/me/favorites/<int:trip_report_info_id>", methods=["OPTIONS"])
    @app.route("/api/me/profile", methods=["OPTIONS"])
    @app.route("/api/profile-avatars", methods=["OPTIONS"])
    @app.route("/api/me/profile/avatar", methods=["OPTIONS"])
    @app.route("/api/me/avatar", methods=["OPTIONS"])
    @app.route("/api/users/<path:username>/avatar", methods=["OPTIONS"])
    @app.route("/api/me/top-four", methods=["OPTIONS"])
    @app.route("/api/me/top-four-eligible", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports/<int:report_id>", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports/<int:report_id>/image", methods=["OPTIONS"])
    @app.route("/api/trip-reports/<int:report_id>", methods=["OPTIONS"])
    @app.route("/api/trip-reports/<int:report_id>/image", methods=["OPTIONS"])
    @app.route("/api/me/wishlist", methods=["OPTIONS"])
    @app.route("/api/me/wishlist/<int:trip_report_info_id>", methods=["OPTIONS"])
    @app.route("/api/users/<path:username>", methods=["OPTIONS"])
    @app.route("/api/friends/<int:friend_user_id>", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>", methods=["OPTIONS"])
    def options_auth(request_id=None, trip_id=None, invite_id=None, gear_id=None, trip_report_info_id=None, user_id=None, report_id=None, username=None, friend_user_id=None):
        # gear_id used by OPTIONS /api/gear/<int:gear_id>; user_id for DELETE collaborators
        return "", 200

    # ----------------------
    # Register auth routes
    # ----------------------
    # Point login at this app and register auth view functions here so they're on the same app we run
    login.app = app
    login.bcrypt.init_app(app)
    app.add_url_rule("/api/signup", view_func=login.signup, methods=["POST"])
    app.add_url_rule("/api/login", view_func=login.login_route, methods=["POST"])
    app.add_url_rule("/api/logout", view_func=login.logout_route, methods=["POST"])
    app.add_url_rule("/api/me", view_func=login.me, methods=["GET"])

    # ----------------------
    # Inventory API
    # ----------------------
    @app.post("/api/gear")
    def create_gear():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401

        payload = request.get_json(silent=True) or {}

        try:
            item_id = add_gear_item(user["id"], payload)
        except ValueError as e:
            return jsonify(error=str(e)), 400

        login.refresh_session_cache(user["id"])
        return jsonify(ok=True, id=item_id), 201

    @app.get("/api/gear")
    def get_gear():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if session.get("gear") is None:
            login.refresh_session_cache(user["id"])
        return jsonify(session["gear"])

    @app.get("/api/gear/<int:gear_id>")
    def get_gear_by_id(gear_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        item = get_gear_item(gear_id, user["id"])
        if not item:
            return jsonify(error="Not found"), 404
        row = dict(item)
        if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
            row["created_at"] = row["created_at"].isoformat()
        if row.get("weight_oz") is not None:
            row["weight_oz"] = float(row["weight_oz"])
        return jsonify(row)

    @app.put("/api/gear/<int:gear_id>")
    def put_gear(gear_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        try:
            update_gear_item(gear_id, user["id"], payload)
            login.refresh_session_cache(user["id"])
            item = get_gear_item(gear_id, user["id"])
            row = dict(item)
            if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
                row["created_at"] = row["created_at"].isoformat()
            if row.get("weight_oz") is not None:
                row["weight_oz"] = float(row["weight_oz"])
            return jsonify(row)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.delete("/api/gear/<int:gear_id>")
    def delete_gear_route(gear_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        try:
            delete_gear_item(gear_id, user["id"])
            login.refresh_session_cache(user["id"])
            return "", 204
        except ValueError:
            return jsonify(error="Not found"), 404

    # ----------------------
    # Friends API
    # ----------------------
    @app.post("/api/friends/request")
    def send_friend_request():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        username = (payload.get("username") or "").strip()
        if not username:
            return jsonify(error="Username is required"), 400
        receiver = get_user_by_username(username)
        if not receiver:
            return jsonify(error="User not found"), 400
        try:
            req_id = create_friend_request(user["id"], receiver["id"])
            return jsonify(ok=True, id=req_id), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/friends/requests")
    def get_friend_requests():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_incoming_requests(user["id"])
        out = []
        for r in rows:
            ca = r.get("created_at")
            out.append({
                "id": r["id"],
                "sender_username": r["sender_username"],
                "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
            })
        return jsonify(out)

    @app.post("/api/friends/requests/<int:request_id>/accept")
    def accept_request(request_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if accept_friend_request(request_id, user["id"]):
            login.refresh_session_cache(user["id"])
            return jsonify(ok=True), 200
        return jsonify(error="Request not found or already handled"), 404

    @app.post("/api/friends/requests/<int:request_id>/decline")
    def decline_request(request_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if decline_friend_request(request_id, user["id"]):
            return jsonify(ok=True), 200
        return jsonify(error="Request not found or already handled"), 404

    @app.get("/api/friends")
    def get_friends():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if session.get("friends") is None:
            login.refresh_session_cache(user["id"])
        return jsonify(session["friends"])

    # ----------------------
    # Favorites (favorite hikes from catalog)
    # ----------------------
    @app.get("/api/me/favorites")
    def get_my_favorites():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_favorite_hikes(user["id"])
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "hike_name": r.get("hike_name") or "",
                "distance": r.get("distance"),
                "elevation_gain": r.get("elevation_gain"),
                "difficulty": r.get("difficulty"),
                "source_url": r.get("source_url"),
            })
        return jsonify(out)

    @app.post("/api/me/favorites")
    def post_my_favorites():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        trip_report_info_id = payload.get("trip_report_info_id")
        if trip_report_info_id is None:
            return jsonify(error="trip_report_info_id required"), 400
        try:
            info_id = int(trip_report_info_id)
        except (TypeError, ValueError):
            return jsonify(error="Invalid trip_report_info_id"), 400
        try:
            add_favorite_hike(user["id"], info_id)
            return jsonify(ok=True), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.delete("/api/me/favorites/<int:trip_report_info_id>")
    def delete_my_favorite(trip_report_info_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        remove_favorite_hike(user["id"], trip_report_info_id)
        return "", 204

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
            "avatar_url_upload": (request.url_root.rstrip("/") + "/api/me/avatar")
            if uploaded
            else None,
            "avatar_url_public": (request.url_root.rstrip("/") + "/api/users/"
                + urllib.parse.quote(str(username), safe="") + "/avatar")
            if uploaded
            else None,
        }

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
        static_dir = os.path.join(app.root_path, "static", PROFILE_AVATAR_DIR_PREFIX)
        full = os.path.normpath(os.path.join(static_dir, rest))
        if not full.startswith(os.path.normpath(static_dir)):
            return None
        if not os.path.isfile(full):
            return None
        return path

    @app.get("/api/profile-avatars")
    def list_profile_avatars():
        """List preset avatar filenames under static/profile_ducks (public)."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        static_dir = os.path.join(app.root_path, "static", PROFILE_AVATAR_DIR_PREFIX)
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
                {"position": r["position"], "trip_report_info_id": r["trip_report_info_id"], "hike_name": r.get("hike_name") or ""}
                for r in top_four
            ],
            "trip_reports": [
                {
                    "id": r["id"],
                    "title": r.get("title") or "",
                    "hike_name": r.get("hike_name") or "",
                    "date_hiked": r["date_hiked"].isoformat() if hasattr(r.get("date_hiked"), "isoformat") else r.get("date_hiked"),
                    "created_at": r["created_at"].isoformat() if hasattr(r.get("created_at"), "isoformat") else r.get("created_at"),
                }
                for r in reports
            ],
        }
        return out

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

    # ----------------------
    # Top four API
    # ----------------------
    @app.get("/api/me/top-four")
    def get_my_top_four():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_top_four_hikes(user["id"])
        out = [{"position": p, "trip_report_info_id": None, "hike_name": None} for p in [1, 2, 3, 4]]
        for r in rows:
            pos = r["position"]
            if 1 <= pos <= 4:
                out[pos - 1] = {
                    "position": pos,
                    "trip_report_info_id": r["trip_report_info_id"],
                    "hike_name": r.get("hike_name") or "",
                }
        return jsonify(out)

    @app.put("/api/me/top-four")
    def put_my_top_four():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        slots = payload.get("slots") if isinstance(payload.get("slots"), list) else []
        try:
            replace_top_four(user["id"], slots)
            rows = list_top_four_hikes(user["id"])
            out = [{"position": p, "trip_report_info_id": None, "hike_name": None} for p in [1, 2, 3, 4]]
            for r in rows:
                pos = r["position"]
                if 1 <= pos <= 4:
                    out[pos - 1] = {"position": pos, "trip_report_info_id": r["trip_report_info_id"], "hike_name": r.get("hike_name") or ""}
            return jsonify(out)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/me/top-four-eligible")
    def get_top_four_eligible():
        """Catalog hikes the user has at least one trip report for (only these can go in top four)."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_top_four_eligible_hikes(user["id"])
        return jsonify([{"id": r["id"], "hike_name": r.get("hike_name") or ""} for r in rows])

    # ----------------------
    # Trip reports API
    # ----------------------
    @app.get("/api/me/trip-reports")
    def get_my_trip_reports():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_user_trip_reports(user["id"])
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "title": r.get("title") or "",
                "trip_report_info_id": r["trip_report_info_id"],
                "hike_name": r.get("hike_name") or "",
                "date_hiked": r["date_hiked"].isoformat() if hasattr(r.get("date_hiked"), "isoformat") else r.get("date_hiked"),
                "created_at": r["created_at"].isoformat() if hasattr(r.get("created_at"), "isoformat") else r.get("created_at"),
            })
        return jsonify(out)

    @app.post("/api/me/trip-reports")
    def post_my_trip_report():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        trip_report_info_id = payload.get("trip_report_info_id")
        title = (payload.get("title") or "").strip()
        body = (payload.get("body") or "").strip() or ""
        date_hiked = payload.get("date_hiked")
        if date_hiked == "":
            date_hiked = None
        if trip_report_info_id is None:
            return jsonify(error="trip_report_info_id required"), 400
        try:
            info_id = int(trip_report_info_id)
        except (TypeError, ValueError):
            return jsonify(error="Invalid trip_report_info_id"), 400
        try:
            report_id = create_user_trip_report(user["id"], info_id, title, body, date_hiked)
            report = get_user_trip_report(report_id, user["id"])
            out = {
                "id": report["id"],
                "title": report.get("title") or "",
                "trip_report_info_id": report["trip_report_info_id"],
                "hike_name": report.get("hike_name") or "",
                "date_hiked": report["date_hiked"].isoformat() if hasattr(report.get("date_hiked"), "isoformat") else report.get("date_hiked"),
                "created_at": report["created_at"].isoformat() if hasattr(report.get("created_at"), "isoformat") else report.get("created_at"),
            }
            return jsonify(out), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/trip-reports/<int:report_id>")
    def get_trip_report_route(report_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        report = get_user_trip_report(report_id, user_id=None)
        if not report:
            return jsonify(error="Not found"), 404
        is_owner = report["user_id"] == user["id"]
        image_uploaded = bool(report.get("image_uploaded"))
        out = {
            "id": report["id"],
            "title": report.get("title") or "",
            "hike_name": report.get("hike_name") or "",
            "trip_report_info_id": report["trip_report_info_id"],
            "body": report.get("body") or "",
            "date_hiked": report["date_hiked"].isoformat() if hasattr(report.get("date_hiked"), "isoformat") else report.get("date_hiked"),
            "created_at": report["created_at"].isoformat() if hasattr(report.get("created_at"), "isoformat") else report.get("created_at"),
            "is_owner": is_owner,
            "image_uploaded": image_uploaded,
        }
        return jsonify(out)

    @app.put("/api/me/trip-reports/<int:report_id>")
    def put_my_trip_report(report_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        trip_report_info_id = payload.get("trip_report_info_id")
        title = (payload.get("title") or "").strip() if "title" in payload else None
        body = (payload.get("body") or "").strip() if "body" in payload else None
        date_hiked = payload.get("date_hiked") if "date_hiked" in payload else None
        if date_hiked == "":
            date_hiked = None
        try:
            update_user_trip_report(report_id, user["id"], trip_report_info_id=trip_report_info_id, title=title, body=body, date_hiked=date_hiked)
            report = get_user_trip_report(report_id, user["id"])
            out = {
                "id": report["id"],
                "title": report.get("title") or "",
                "hike_name": report.get("hike_name") or "",
                "trip_report_info_id": report["trip_report_info_id"],
                "body": report.get("body") or "",
                "date_hiked": report["date_hiked"].isoformat() if hasattr(report.get("date_hiked"), "isoformat") else report.get("date_hiked"),
                "is_owner": True,
            }
            return jsonify(out)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.post("/api/me/trip-reports/<int:report_id>/image")
    def post_trip_report_image(report_id):
        """Upload trip report image (multipart file). Owner only. Max 5MB."""
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
            set_trip_report_image_upload(report_id, user["id"], data, media_type)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        return jsonify({"ok": True})

    @app.get("/api/trip-reports/<int:report_id>/image")
    def get_trip_report_image(report_id):
        """Serve trip report image. No auth so img src works from static pages."""
        payload = get_trip_report_image_payload(report_id)
        if not payload:
            return "", 204
        return Response(
            payload["bytes"],
            mimetype=payload["media_type"],
            headers={"Cache-Control": "public, max-age=3600"},
        )

    @app.delete("/api/me/trip-reports/<int:report_id>")
    def delete_my_trip_report(report_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        try:
            delete_user_trip_report(report_id, user["id"])
            return "", 204
        except ValueError:
            return jsonify(error="Not found"), 404

    # ----------------------
    # Wishlist API
    # ----------------------
    @app.get("/api/me/wishlist")
    def get_my_wishlist():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_wishlist(user["id"])
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "hike_name": r.get("hike_name") or "",
                "distance": r.get("distance"),
                "elevation_gain": r.get("elevation_gain"),
                "difficulty": r.get("difficulty"),
                "source_url": r.get("source_url"),
            })
        return jsonify(out)

    @app.post("/api/me/wishlist")
    def post_my_wishlist():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        trip_report_info_id = payload.get("trip_report_info_id")
        if trip_report_info_id is None:
            return jsonify(error="trip_report_info_id required"), 400
        try:
            info_id = int(trip_report_info_id)
        except (TypeError, ValueError):
            return jsonify(error="Invalid trip_report_info_id"), 400
        try:
            add_wishlist_item(user["id"], info_id)
            return jsonify(ok=True), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.delete("/api/me/wishlist/<int:trip_report_info_id>")
    def delete_my_wishlist_item(trip_report_info_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        remove_wishlist_item(user["id"], trip_report_info_id)
        return "", 204

    # ----------------------
    # Unfriend / Cancel friend request
    # ----------------------
    @app.delete("/api/friends/<int:friend_user_id>")
    def delete_friend(friend_user_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if remove_friend(user["id"], friend_user_id):
            login.refresh_session_cache(user["id"])
            return "", 204
        return jsonify(error="Not friends or not found"), 404

    @app.delete("/api/friends/requests/<int:request_id>")
    def cancel_friend_request_route(request_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if cancel_friend_request(request_id, user["id"]):
            login.refresh_session_cache(user["id"])
            return "", 204
        return jsonify(error="Request not found or already handled"), 404

    # ----------------------
    # Trips API
    # ----------------------
    def _trip_to_json(t):
        out = {"id": t["id"], "trip_name": t["trip_name"], "trail_name": t.get("trail_name"), "activity_type": t.get("activity_type"), "creator_username": t.get("creator_username"), "notes": (t.get("notes") or "")}
        if t.get("trip_report_info_id") is not None:
            out["trip_report_info_id"] = t["trip_report_info_id"]
        ca = t.get("created_at")
        out["created_at"] = ca.isoformat() if hasattr(ca, "isoformat") else ca
        idate = t.get("intended_start_date")
        out["intended_start_date"] = idate.isoformat() if hasattr(idate, "isoformat") else idate if idate else None
        return out

    @app.post("/api/trips")
    def post_trip():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        payload = request.get_json(silent=True) or {}
        try:
            trip_id = create_trip(user["id"], payload)
            trip = get_trip(trip_id)
            login.refresh_session_cache(user["id"])
            return jsonify(_trip_to_json(trip)), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/locations")
    def get_locations():
        """Return location catalog (trip_report_info) for trip creation dropdown/search."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_trip_report_info_for_selection()
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "hike_name": r.get("hike_name") or "",
                "distance": r.get("distance"),
                "elevation_gain": r.get("elevation_gain"),
                "difficulty": r.get("difficulty"),
                "source_url": r.get("source_url"),
            })
        return jsonify(out)

    @app.get("/api/trips")
    def get_trips():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if session.get("trips") is None:
            login.refresh_session_cache(user["id"])
        return jsonify(session["trips"])

    @app.get("/api/trips/<int:trip_id>")
    def get_trip_route(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        trip = get_trip(trip_id)
        if not trip:
            return jsonify(error="Not found"), 404
        out = _trip_to_json(trip)
        out["is_creator"] = trip["creator_id"] == user["id"]
        return jsonify(out)

    @app.put("/api/trips/<int:trip_id>")
    def put_trip(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        payload = request.get_json(silent=True) or {}
        try:
            update_trip(trip_id, user["id"], payload)
            login.refresh_session_cache(user["id"])
            login.invalidate_trip_dashboard_cache(trip_id)
            trip = get_trip(trip_id)
            out = _trip_to_json(trip)
            out["is_creator"] = trip["creator_id"] == user["id"]
            return jsonify(out)
        except ValueError as e:
            err = str(e)
            return jsonify(error=err), (403 if "creator" in err.lower() else 400)

    @app.delete("/api/trips/<int:trip_id>")
    def delete_trip_route(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        try:
            delete_trip(trip_id, user["id"])
            login.refresh_session_cache(user["id"])
            login.invalidate_trip_dashboard_cache()
            return "", 204
        except ValueError as e:
            return jsonify(error=str(e)), 403

    @app.post("/api/trips/<int:trip_id>/leave")
    def leave_trip_route(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        try:
            leave_trip(trip_id, user["id"])
            login.refresh_session_cache(user["id"])
            login.invalidate_trip_dashboard_cache()
            return "", 204
        except ValueError as e:
            return jsonify(error=str(e)), 403

    def _build_trip_dashboard(trip_id, user):
        """Build full dashboard payload for a trip (trip, collaborators, gear, checklist, etc.)."""
        trip = get_trip(trip_id)
        if not trip:
            return None
        trip_json = _trip_to_json(trip)
        trip_json["is_creator"] = trip["creator_id"] == user["id"]

        my_invites = list_incoming_trip_invites(user["id"])
        pending_invite = next((i for i in my_invites if i["trip_id"] == trip_id), None)
        if pending_invite:
            ca = pending_invite.get("created_at")
            pending_invite = {
                "id": pending_invite["id"],
                "trip_id": pending_invite["trip_id"],
                "trip_name": pending_invite.get("trip_name"),
                "inviter_username": pending_invite.get("inviter_username"),
                "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
            }
        else:
            pending_invite = None

        collaborators = [
            {"id": c["id"], "username": c["username"], "role": c["role"]}
            for c in list_trip_collaborators(trip_id)
        ]

        pending_invites = []
        friends = []
        if trip_json.get("is_creator"):
            rows = list_trip_invites_pending(trip_id)
            for r in rows:
                ca = r.get("created_at")
                pending_invites.append({
                    "id": r["id"],
                    "invitee_id": r["invitee_id"],
                    "invitee_username": r["invitee_username"],
                    "inviter_username": r["inviter_username"],
                    "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
                })
            all_friends = list_friends(user["id"])
            collab_ids = {c["id"] for c in collaborators}
            pending_invitee_ids = {p["invitee_id"] for p in pending_invites}
            friends = [
                {"id": f["id"], "username": f["username"]}
                for f in all_friends
                if f["id"] not in collab_ids and f["id"] not in pending_invitee_ids
            ]

        gear_pool = get_trip_gear_pool(trip_id)
        gear_pool = [dict(row) for row in gear_pool]
        for row in gear_pool:
            if row.get("weight_oz") is not None:
                row["weight_oz"] = float(row["weight_oz"])

        assigned_gear = get_trip_assigned_gear(trip_id)
        assigned_gear = [dict(row) for row in assigned_gear]
        for row in assigned_gear:
            if row.get("weight_oz") is not None:
                row["weight_oz"] = float(row["weight_oz"])

        summary = get_trip_requirement_summary(trip_id)
        checklist = []
        if summary:
            for s in summary:
                checklist.append({
                    "requirement_type_id": s["requirement_type_id"],
                    "requirement_key": s["requirement_key"],
                    "requirement_display_name": s["requirement_display_name"],
                    "rule": s["rule"],
                    "quantity": s["quantity"],
                    "n_persons": s["n_persons"],
                    "required_count": s["required_count"],
                    "covered_count": s["covered_count"],
                    "status": s["status"],
                })

        trip_report_info = get_trip_report_info_for_trip(trip_id)
        location_summary = None
        if trip_report_info:
            location_summary = {
                "hike_name": trip_report_info.get("hike_name"),
                "summarized_description": trip_report_info.get("summarized_description"),
                "source_url": trip_report_info.get("source_url"),
                "distance": trip_report_info.get("distance"),
                "elevation_gain": trip_report_info.get("elevation_gain"),
                "highpoint": trip_report_info.get("highpoint"),
                "difficulty": trip_report_info.get("difficulty"),
                "lat": trip_report_info.get("lat"),
                "long": trip_report_info.get("long"),
                "trip_report_1": trip_report_info.get("trip_report_1"),
                "trip_report_2": trip_report_info.get("trip_report_2"),
            }

        return {
            "trip": trip_json,
            "pending_invite": pending_invite,
            "collaborators": collaborators,
            "pending_invites": pending_invites,
            "friends": friends,
            "gear_pool": gear_pool,
            "assigned_gear": assigned_gear,
            "checklist": checklist,
            "location_summary": location_summary,
        }

    @app.get("/api/trips/<int:trip_id>/dashboard")
    def get_trip_dashboard(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        cached = (session.get("trip_dashboard") or {}).get(str(trip_id))
        if cached is not None:
            return jsonify(cached)
        payload = _build_trip_dashboard(trip_id, user)
        if payload is None:
            return jsonify(error="Not found"), 404
        if "trip_dashboard" not in session:
            session["trip_dashboard"] = {}
        session["trip_dashboard"][str(trip_id)] = payload
        return jsonify(payload)

    def _fetch_nws_forecast(lat, lon, trip_date_str):
        """Fetch NWS 7-day forecast for lat,lon. Return period for trip_date if in range, else first period.
        Returns dict with for_date, is_trip_date, temperature, temperatureUnit, shortForecast, detailedForecast, periodName
        or None on error.
        """
        try:
            lat_f = float(str(lat).strip())
            lon_f = float(str(lon).strip())
            if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
                return None
        except (TypeError, ValueError):
            return None
        lat_s = f"{lat_f:.2f}"
        lon_s = f"{lon_f:.2f}"
        points_url = f"https://api.weather.gov/points/{lat_s},{lon_s}"
        headers = {"User-Agent": "TrailFeathers/1.0 (https://github.com/trailfeathers)"}
        req = urllib.request.Request(points_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError):
            return None
        props = data.get("properties") or {}
        forecast_url = (props.get("forecast") or "").strip()
        if not forecast_url:
            return None
        req2 = urllib.request.Request(forecast_url, headers=headers)
        try:
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                forecast_data = json.loads(resp2.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError):
            return None
        periods = (forecast_data.get("properties") or {}).get("periods") or []
        if not periods:
            return None
        trip_date = None
        if trip_date_str:
            if hasattr(trip_date_str, "isoformat"):
                trip_date = trip_date_str
            else:
                s = str(trip_date_str).strip()[:10]
                try:
                    trip_date = datetime.strptime(s, "%Y-%m-%d").date()
                except ValueError:
                    pass
        chosen = periods[0]
        is_trip_date = False
        if trip_date:
            for p in periods:
                start_s = (p.get("startTime") or "").strip()
                end_s = (p.get("endTime") or "").strip()
                if not start_s:
                    continue
                try:
                    start_dt = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
                    start_d = start_dt.date()
                except (ValueError, TypeError):
                    continue
                if end_s:
                    try:
                        end_dt = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
                        end_d = end_dt.date()
                    except (ValueError, TypeError):
                        end_d = start_d
                else:
                    end_d = start_d
                if start_d <= trip_date <= end_d:
                    chosen = p
                    is_trip_date = True
                    break
        for_date = trip_date.isoformat() if trip_date else (chosen.get("startTime") or "")[:10]
        if not for_date or len(for_date) > 10:
            for_date = (chosen.get("startTime") or "")[:10]
        return {
            "for_date": for_date,
            "is_trip_date": is_trip_date,
            "temperature": chosen.get("temperature"),
            "temperatureUnit": chosen.get("temperatureUnit") or "F",
            "shortForecast": chosen.get("shortForecast") or "",
            "detailedForecast": chosen.get("detailedForecast") or "",
            "periodName": chosen.get("name") or "",
        }

    @app.get("/api/trips/<int:trip_id>/weather")
    def get_trip_weather(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        trip = get_trip(trip_id)
        if not trip:
            return jsonify(error="Not found"), 404
        trip_report_info = get_trip_report_info_for_trip(trip_id)
        if not trip_report_info:
            return jsonify(error="no_coordinates"), 200
        lat = trip_report_info.get("lat")
        lon = trip_report_info.get("long")
        if lat is None or lon is None or not str(lat).strip() or not str(lon).strip():
            return jsonify(error="no_coordinates"), 200
        intended_start = trip.get("intended_start_date")
        if hasattr(intended_start, "isoformat"):
            intended_start = intended_start.isoformat()
        result = _fetch_nws_forecast(lat, lon, intended_start)
        if result is None:
            return jsonify(error="forecast_unavailable", message="Weather service unavailable"), 200
        return jsonify(result), 200

    @app.get("/api/trips/<int:trip_id>/checklist")
    def get_trip_checklist(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        trip = get_trip(trip_id)
        if not trip:
            return jsonify(error="Not found"), 404
        summary = get_trip_requirement_summary(trip_id)
        if summary is None:
            return jsonify([])
        out = []
        for s in summary:
            item = {
                "requirement_type_id": s["requirement_type_id"],
                "requirement_key": s["requirement_key"],
                "requirement_display_name": s["requirement_display_name"],
                "rule": s["rule"],
                "quantity": s["quantity"],
                "n_persons": s["n_persons"],
                "required_count": s["required_count"],
                "covered_count": s["covered_count"],
                "status": s["status"],
            }
            out.append(item)
        return jsonify(out)

    @app.get("/api/requirement-types")
    def get_requirement_types():
        """Return all requirement types for gear type dropdown and forms."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        types = list_requirement_types()
        return jsonify([{"id": t["id"], "key": t["key"], "display_name": t["display_name"]} for t in types])

    @app.get("/api/trips/<int:trip_id>/collaborators")
    def get_trip_collaborators(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        collab = list_trip_collaborators(trip_id)
        return jsonify([{"id": c["id"], "username": c["username"], "role": c["role"]} for c in collab])

    @app.post("/api/trips/<int:trip_id>/invites")
    def post_trip_invite(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        trip = get_trip(trip_id)
        if not trip or trip["creator_id"] != user["id"]:
            return jsonify(error="Only the trip creator can invite people"), 403
        payload = request.get_json(silent=True) or {}
        invitee_id = payload.get("user_id")
        username = (payload.get("username") or "").strip()
        if invitee_id is None and username:
            u = get_user_by_username(username)
            invitee_id = u["id"] if u else None
        if invitee_id is None:
            return jsonify(error="user_id or username required"), 400
        try:
            invitee_id = int(invitee_id)
        except (TypeError, ValueError):
            return jsonify(error="Invalid user_id"), 400
        friend_ids = [f["id"] for f in list_friends(user["id"])]
        if invitee_id not in friend_ids:
            return jsonify(error="Can only invite friends"), 400
        try:
            invite_id = create_trip_invite(trip_id, user["id"], invitee_id)
            login.invalidate_trip_dashboard_cache(trip_id)
            return jsonify(ok=True, id=invite_id), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/trips/<int:trip_id>/invites")
    def get_trip_invites(trip_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        trip = get_trip(trip_id)
        if not trip or trip["creator_id"] != user["id"]:
            return jsonify(error="Only the trip creator can view pending invites"), 403
        rows = list_trip_invites_pending(trip_id)
        out = []
        for r in rows:
            ca = r.get("created_at")
            out.append({
                "id": r["id"],
                "invitee_id": r["invitee_id"],
                "invitee_username": r["invitee_username"],
                "inviter_username": r["inviter_username"],
                "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
            })
        return jsonify(out)

    @app.get("/api/trip-invites")
    def get_my_trip_invites():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_incoming_trip_invites(user["id"])
        out = []
        for r in rows:
            ca = r.get("created_at")
            out.append({
                "id": r["id"],
                "trip_id": r["trip_id"],
                "trip_name": r["trip_name"],
                "inviter_username": r["inviter_username"],
                "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
            })
        return jsonify(out)

    @app.post("/api/trip-invites/<int:invite_id>/accept")
    def accept_trip_invite_route(invite_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if accept_trip_invite(invite_id, user["id"]):
            login.refresh_session_cache(user["id"])
            tid = get_trip_id_for_invite(invite_id)
            if tid is not None:
                login.invalidate_trip_dashboard_cache(tid)
            return jsonify(ok=True), 200
        return jsonify(error="Invite not found or already responded to"), 404

    @app.post("/api/trip-invites/<int:invite_id>/decline")
    def decline_trip_invite_route(invite_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if decline_trip_invite(invite_id, user["id"]):
            tid = get_trip_id_for_invite(invite_id)
            if tid is not None:
                login.invalidate_trip_dashboard_cache(tid)
            return jsonify(ok=True), 200
        return jsonify(error="Invite not found or already responded to"), 404

    @app.delete("/api/trips/<int:trip_id>/collaborators/<int:user_id>")
    def delete_trip_collaborator(trip_id, user_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        trip = get_trip(trip_id)
        if not trip:
            return jsonify(error="Not found"), 404
        if trip["creator_id"] != user["id"]:
            return jsonify(error="Only the trip creator can remove members"), 403
        try:
            remove_trip_collaborator(trip_id, user_id, user["id"])
            login.invalidate_trip_dashboard_cache(trip_id)
            return "", 200
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.delete("/api/trip-invites/<int:invite_id>")
    def cancel_trip_invite_route(invite_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        trip_id = get_trip_id_for_invite(invite_id)
        if trip_id is None:
            return jsonify(error="Invite not found"), 404
        trip = get_trip(trip_id)
        if not trip or trip["creator_id"] != user["id"]:
            return jsonify(error="Only the trip creator can cancel invites"), 404
        if cancel_trip_invite(invite_id, user["id"]):
            login.invalidate_trip_dashboard_cache(trip_id)
            return "", 200
        return jsonify(error="Invite not found or already responded to"), 404

    # ----------------------
    # Trip Gear API
    # ----------------------
    @app.get("/api/trips/<int:trip_id>/gear/pool")
    def get_trip_gear_pool_route(trip_id):
        """Get all available gear from trip collaborators"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        gear_pool = get_trip_gear_pool(trip_id)
        return jsonify(gear_pool)

    @app.get("/api/trips/<int:trip_id>/gear")
    def get_trip_assigned_gear_route(trip_id):
        """Get gear already assigned to this trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        assigned_gear = get_trip_assigned_gear(trip_id)
        return jsonify(assigned_gear)

    @app.post("/api/trips/<int:trip_id>/gear/<int:gear_id>")
    def assign_gear_to_trip_route(trip_id, gear_id):
        """Assign a piece of gear to a trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        try:
            assign_gear_to_trip(trip_id, gear_id)
            login.invalidate_trip_dashboard_cache(trip_id)
            return jsonify(ok=True), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.delete("/api/trips/<int:trip_id>/gear/<int:gear_id>")
    def unassign_gear_from_trip_route(trip_id, gear_id):
        """Remove gear assignment from a trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        unassign_gear_from_trip(trip_id, gear_id)
        login.invalidate_trip_dashboard_cache(trip_id)
        return jsonify(ok=True), 200

    # ----------------------
    # Health check
    # ----------------------
    @app.get("/")
    def health():
        return "OK"

    return app


# Gunicorn entry point
app = create_app()
