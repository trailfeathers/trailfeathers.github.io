import os
from datetime import timedelta

from flask import Flask, request, jsonify, session
from flask_cors import CORS

# Import auth routes (this file defines routes on an app instance)
from auth import login

# Import gear, friend, and trip DB helpers
from database.database import (
    add_gear_item,
    list_gear,
    get_user_by_username,
    create_friend_request,
    list_incoming_requests,
    accept_friend_request,
    decline_friend_request,
    list_friends,
    create_trip,
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
    @app.route("/api/friends/request", methods=["OPTIONS"])
    @app.route("/api/friends/requests", methods=["OPTIONS"])
    @app.route("/api/friends", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/accept", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/checklist", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/collaborators", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/accept", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/pool", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/<int:gear_id>", methods=["OPTIONS"])
    def options_auth(request_id=None, trip_id=None, invite_id=None, gear_id=None):
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
    # Trips API
    # ----------------------
    def _trip_to_json(t):
        out = {"id": t["id"], "trip_name": t["trip_name"], "trail_name": t.get("trail_name"), "activity_type": t.get("activity_type"), "creator_username": t.get("creator_username")}
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
        from checklists.requirements import CHECKLISTS
        activity_type = (trip.get("activity_type") or "").strip()
        items = CHECKLISTS.get(activity_type, [])
        return jsonify(items)

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
            return jsonify(ok=True), 200
        return jsonify(error="Invite not found or already responded to"), 404

    @app.post("/api/trip-invites/<int:invite_id>/decline")
    def decline_trip_invite_route(invite_id):
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if decline_trip_invite(invite_id, user["id"]):
            return jsonify(ok=True), 200
        return jsonify(error="Invite not found or already responded to"), 404

    # ----------------------
    # Trip Gear API
    # ----------------------
    @app.get("/api/trips/<int:trip_id>/gear/pool")
    def get_trip_gear_pool(trip_id):
        """Get all available gear from trip collaborators"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        
        from database.database import get_trip_gear_pool
        gear_pool = get_trip_gear_pool(trip_id)
        return jsonify(gear_pool)
    
    @app.get("/api/trips/<int:trip_id>/gear")
    def get_trip_assigned_gear(trip_id):
        """Get gear already assigned to this trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        
        from database.database import get_trip_assigned_gear
        assigned_gear = get_trip_assigned_gear(trip_id)
        return jsonify(assigned_gear)
    
    @app.post("/api/trips/<int:trip_id>/gear/<int:gear_id>")
    def assign_gear_to_trip(trip_id, gear_id):
        """Assign a piece of gear to a trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        
        from database.database import assign_gear_to_trip as db_assign
        try:
            db_assign(trip_id, gear_id)
            return jsonify(ok=True), 201
        except ValueError as e:
            return jsonify(error=str(e)), 400
    
    @app.delete("/api/trips/<int:trip_id>/gear/<int:gear_id>")
    def unassign_gear_from_trip(trip_id, gear_id):
        """Remove gear assignment from a trip"""
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401
        if not user_has_trip_access(user["id"], trip_id):
            return jsonify(error="Not found"), 404
        
        from database.database import unassign_gear_from_trip
        unassign_gear_from_trip(trip_id, gear_id)
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
