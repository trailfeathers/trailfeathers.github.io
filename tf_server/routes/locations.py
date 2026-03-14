"""
TrailFeathers - Locations (hike catalog) API: GET /api/locations returns trip_report_info for dropdowns.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from flask import jsonify

from db import list_trip_report_info_for_selection


def register(app, login):
    """Register locations route; login for require_auth()."""

    @app.get("/api/locations")
    def get_locations():
        """Return location catalog (trip_report_info) for dropdowns."""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        rows = list_trip_report_info_for_selection()
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

