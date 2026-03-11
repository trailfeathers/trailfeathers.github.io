from flask import Response, jsonify, request

from database.database import (
    create_user_trip_report,
    delete_user_trip_report,
    get_trip_report_image_payload,
    get_user_trip_report,
    list_user_trip_reports,
    set_trip_report_image_upload,
    update_user_trip_report,
)


def register(app, login):
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
            out.append(
                {
                    "id": r["id"],
                    "title": r.get("title") or "",
                    "trip_report_info_id": r["trip_report_info_id"],
                    "hike_name": r.get("hike_name") or "",
                    "date_hiked": r["date_hiked"].isoformat()
                    if hasattr(r.get("date_hiked"), "isoformat")
                    else r.get("date_hiked"),
                    "created_at": r["created_at"].isoformat()
                    if hasattr(r.get("created_at"), "isoformat")
                    else r.get("created_at"),
                }
            )
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
                "date_hiked": report["date_hiked"].isoformat()
                if hasattr(report.get("date_hiked"), "isoformat")
                else report.get("date_hiked"),
                "created_at": report["created_at"].isoformat()
                if hasattr(report.get("created_at"), "isoformat")
                else report.get("created_at"),
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
            "date_hiked": report["date_hiked"].isoformat()
            if hasattr(report.get("date_hiked"), "isoformat")
            else report.get("date_hiked"),
            "created_at": report["created_at"].isoformat()
            if hasattr(report.get("created_at"), "isoformat")
            else report.get("created_at"),
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
            update_user_trip_report(
                report_id,
                user["id"],
                trip_report_info_id=trip_report_info_id,
                title=title,
                body=body,
                date_hiked=date_hiked,
            )
            report = get_user_trip_report(report_id, user["id"])
            out = {
                "id": report["id"],
                "title": report.get("title") or "",
                "hike_name": report.get("hike_name") or "",
                "trip_report_info_id": report["trip_report_info_id"],
                "body": report.get("body") or "",
                "date_hiked": report["date_hiked"].isoformat()
                if hasattr(report.get("date_hiked"), "isoformat")
                else report.get("date_hiked"),
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

