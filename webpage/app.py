import os
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import auth routes (this file defines routes on an app instance)
import login

# Import inventory DB helpers
from database.database_inventory.database_inventory_pg import (
    add_gear_item,
    list_gear,
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
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = bool(os.getenv("RENDER"))

    # ----------------------
    # CORS (sessions!)
    # ----------------------
    CORS(
        app,
        supports_credentials=True,
        origins=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            os.getenv("FRONTEND_URL"),
        ],
    )

    # ----------------------
    # Register auth routes
    # ----------------------
    # login.py already defines routes on its own Flask app,
    # so we mount them onto this app via blueprint-style reassignment
    login.app = app
    login.bcrypt.init_app(app)

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
            item_id = add_gear_item(user["username"], payload)
        except ValueError as e:
            return jsonify(error=str(e)), 400

        return jsonify(ok=True, id=item_id), 201

    @app.get("/api/gear")
    def get_gear():
        user = login.require_auth()
        if not user:
            return jsonify(error="Not logged in"), 401

        items = list_gear(user["username"])
        return jsonify(items)

    # ----------------------
    # Health check
    # ----------------------
    @app.get("/")
    def health():
        return "OK"

    return app


# Gunicorn entry point
app = create_app()
