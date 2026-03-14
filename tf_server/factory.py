"""
TrailFeathers - Flask application factory: creates app, config (CORS, session), registers auth and feature routes.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from auth import login


def create_app():
    app = Flask(__name__)

    # ----------------------
    # Config
    # ----------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")

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

    # ----------------------
    # Preflight OPTIONS must return 2xx for CORS
    # ----------------------
    from .routes.options import register as register_options

    register_options(app)

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
    # Register feature routes
    # ----------------------
    from .routes.gear import register as register_gear
    from .routes.friends import register as register_friends
    from .routes.profile import register as register_profile
    from .routes.top_four import register as register_top_four
    from .routes.trip_reports import register as register_trip_reports
    from .routes.wishlist import register as register_wishlist
    from .routes.locations import register as register_locations
    from .routes.trips import register as register_trips
    from .routes.health import register as register_health

    register_gear(app, login)
    register_friends(app, login)
    register_profile(app, login)
    register_top_four(app, login)
    register_trip_reports(app, login)
    register_wishlist(app, login)
    register_locations(app, login)
    register_trips(app, login)
    register_health(app)

    return app

