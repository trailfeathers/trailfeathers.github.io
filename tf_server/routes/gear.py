"""
Gear (inventory) API. CRUD for the current user's gear items. Endpoints:
POST /api/gear, GET /api/gear (from session cache), GET/PUT/DELETE /api/gear/<id>.
Session gear cache refreshed on create/update/delete.
"""
from flask import jsonify, request, session

from db import (
    add_gear_item,
    delete_gear_item,
    get_gear_item,
    update_gear_item,
)


def register(app, login):
    """Register gear routes; login for require_auth() and refresh_session_cache()."""

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

