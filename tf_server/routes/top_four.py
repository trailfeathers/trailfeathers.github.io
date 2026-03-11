from flask import jsonify, request

from database.database import (
    list_top_four_eligible_hikes,
    list_top_four_hikes,
    replace_top_four,
)


def register(app, login):
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
                    "latest_report_id": r.get("latest_report_id"),
                    "image_report_id": r.get("image_report_id"),
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
                    out[pos - 1] = {
                        "position": pos,
                        "trip_report_info_id": r["trip_report_info_id"],
                        "hike_name": r.get("hike_name") or "",
                        "latest_report_id": r.get("latest_report_id"),
                        "image_report_id": r.get("image_report_id"),
                    }
            return jsonify(out)
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/me/top-four-eligible")
    def get_top_four_eligible():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_top_four_eligible_hikes(user["id"])
        return jsonify(
            [{"id": r["id"], "hike_name": r.get("hike_name") or ""} for r in rows]
        )

