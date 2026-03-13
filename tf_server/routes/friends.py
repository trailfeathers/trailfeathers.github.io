from flask import jsonify, request, session

from db import (
    accept_friend_request,
    add_favorite_hike,
    cancel_friend_request,
    create_friend_request,
    decline_friend_request,
    get_user_by_username,
    list_favorite_hikes,
    list_incoming_requests,
    remove_favorite_hike,
    remove_friend,
)


def register(app, login):
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
            out.append(
                {
                    "id": r["id"],
                    "sender_username": r["sender_username"],
                    "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
                }
            )
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
            out.append(
                {
                    "id": r["id"],
                    "hike_name": r.get("hike_name") or "",
                    "distance": r.get("distance"),
                    "elevation_gain": r.get("elevation_gain"),
                    "difficulty": r.get("difficulty"),
                    "source_url": r.get("source_url"),
                }
            )
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

