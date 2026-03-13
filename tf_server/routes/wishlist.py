from flask import jsonify, request

from db import add_wishlist_item, list_wishlist, remove_wishlist_item


def register(app, login):
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

