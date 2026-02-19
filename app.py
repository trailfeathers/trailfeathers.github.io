import os
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import auth routes (this file defines routes on an app instance)
from auth import login

# Import gear and friend DB helpers
from database.database import (
    add_gear_item,
    list_gear,
    get_user_by_username,
    create_friend_request,
    list_incoming_requests,
    accept_friend_request,
    decline_friend_request,
    list_friends,
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
    def options_auth(request_id=None):
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

        return jsonify(ok=True, id=item_id), 201

    @app.get("/api/gear")
    def get_gear():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401

        items = list_gear(user["id"])
        return jsonify(items)

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
        friends = list_friends(user["id"])
        return jsonify([{"id": f["id"], "username": f["username"]} for f in friends])

    # ----------------------
    # Health check
    # ----------------------
    @app.get("/")
    def health():
        return "OK"

    return app


# Gunicorn entry point
app = create_app()
