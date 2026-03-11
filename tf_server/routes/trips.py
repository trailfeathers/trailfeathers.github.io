import json
import urllib.error
import urllib.request
from datetime import datetime

from flask import jsonify, request, session

from database.database import (
    accept_trip_invite,
    assign_gear_to_trip,
    cancel_trip_invite,
    create_trip,
    create_trip_invite,
    decline_trip_invite,
    delete_trip,
    get_trip,
    get_trip_assigned_gear,
    get_trip_gear_pool,
    get_trip_id_for_invite,
    get_trip_report_info_for_trip,
    get_trip_requirement_summary,
    get_user_by_username,
    has_pending_invite_to_trip,
    leave_trip,
    list_friends,
    list_incoming_trip_invites,
    list_requirement_types,
    list_trip_collaborators,
    list_trip_invites_pending,
    remove_trip_collaborator,
    unassign_gear_from_trip,
    update_trip,
    user_has_trip_access,
)


def register(app, login):
    # ----------------------
    # Trips API
    # ----------------------
    def _trip_to_json(t):
        out = {
            "id": t["id"],
            "trip_name": t["trip_name"],
            "trail_name": t.get("trail_name"),
            "activity_type": t.get("activity_type"),
            "creator_username": t.get("creator_username"),
            "notes": (t.get("notes") or ""),
        }
        if t.get("trip_report_info_id") is not None:
            out["trip_report_info_id"] = t["trip_report_info_id"]
        ca = t.get("created_at")
        out["created_at"] = ca.isoformat() if hasattr(ca, "isoformat") else ca
        idate = t.get("intended_start_date")
        out["intended_start_date"] = (
            idate.isoformat() if hasattr(idate, "isoformat") else idate if idate else None
        )
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
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(
            user["id"], trip_id
        ):
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
                pending_invites.append(
                    {
                        "id": r["id"],
                        "invitee_id": r["invitee_id"],
                        "invitee_username": r["invitee_username"],
                        "inviter_username": r["inviter_username"],
                        "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
                    }
                )
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
                checklist.append(
                    {
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
                )

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
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(
            user["id"], trip_id
        ):
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
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(
            user["id"], trip_id
        ):
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
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(
            user["id"], trip_id
        ):
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
        if not user_has_trip_access(user["id"], trip_id) and not has_pending_invite_to_trip(
            user["id"], trip_id
        ):
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
            out.append(
                {
                    "id": r["id"],
                    "invitee_id": r["invitee_id"],
                    "invitee_username": r["invitee_username"],
                    "inviter_username": r["inviter_username"],
                    "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
                }
            )
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
            out.append(
                {
                    "id": r["id"],
                    "trip_id": r["trip_id"],
                    "trip_name": r.get("trip_name") or "",
                    "inviter_username": r.get("inviter_username") or "",
                    "created_at": ca.isoformat() if hasattr(ca, "isoformat") else ca,
                }
            )
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

