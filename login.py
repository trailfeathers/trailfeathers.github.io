import os
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from datetime import timedelta

app = Flask(__name__)
bcrypt = Bcrypt(app)

# --- Production secret key (stable across restarts) ---
# Set this on Render as an environment variable named SECRET_KEY.
# For local dev, it falls back to a dev key.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")

# Session config (Flask's default cookie-based sessions)
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)

# Cookie security settings
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Render typically provides HTTPS, so secure cookies should be enabled in production.
# Render sets RENDER externally; this is a common pattern to detect the platform.
app.config["SESSION_COOKIE_SECURE"] = bool(os.getenv("RENDER"))

# --- Fake "DB" for demo ---
users_by_email = {}     # email -> user dict
users_by_username = {}  # username -> user dict
users_by_id = {}        # id -> user dict
next_id = 1


def require_auth():
    """Helper for protected routes."""
    uid = session.get("user_id")
    if not uid or uid not in users_by_id:
        return None
    return users_by_id[uid]


@app.post("/api/signup")
def signup():
    global next_id
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not email or not username or not password:
        return jsonify(error="Missing email, username, or password"), 400

    if email in users_by_email:
        return jsonify(error="Email already exists"), 409

    if username in users_by_username:
        return jsonify(error="Username already exists"), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = {"id": next_id, "email": email, "username": username, "pw_hash": pw_hash}
    next_id += 1

    users_by_email[email] = user
    users_by_username[username] = user
    users_by_id[user["id"]] = user

    # Auto-login after signup
    session["user_id"] = user["id"]
    session.permanent = True

    return jsonify(ok=True, user={"id": user["id"], "email": user["email"], "username": user["username"]})


@app.post("/api/login")
def login_route():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(error="Missing email or password"), 400

    user = users_by_email.get(email)
    if not user:
        return jsonify(error="Invalid credentials"), 401

    if not bcrypt.check_password_hash(user["pw_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    session["user_id"] = user["id"]
    session.permanent = True
    return jsonify(ok=True)


@app.post("/api/logout")
def logout_route():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    user = require_auth()
    if not user:
        return jsonify(error="Not logged in"), 401
    return jsonify(id=user["id"], email=user["email"], username=user["username"])


if __name__ == "__main__":
    # Local dev only. On Render, use Gunicorn with $PORT.
    app.run(debug=True, host="0.0.0.0", port=5000)
