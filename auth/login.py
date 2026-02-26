import os
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from datetime import timedelta

from database.database import (
    get_user_by_id,
    get_user_by_username,
    create_user,
    user_exists_by_username,
    list_gear,
    list_friends,
    list_trips_for_user,
)

app = Flask(__name__)
bcrypt = Bcrypt(app)

# --- Secret Key ---
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "dev-insecure-secret-key-change-me"
)

# Session config
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.getenv("RENDER"))


def _serialize_gear(items):
    """Convert gear list to JSON-serializable dicts for session."""
    out = []
    for g in items:
        row = dict(g)
        ca = row.get("created_at")
        if hasattr(ca, "isoformat"):
            row["created_at"] = ca.isoformat()
        if row.get("weight_oz") is not None:
            row["weight_oz"] = float(row["weight_oz"])
        out.append(row)
    return out


def _serialize_trip(t):
    """Convert one trip to JSON-serializable dict for session."""
    out = {
        "id": t["id"],
        "trip_name": t["trip_name"],
        "trail_name": t.get("trail_name"),
        "activity_type": t.get("activity_type"),
        "creator_id": t.get("creator_id"),
        "creator_username": t.get("creator_username"),
    }
    ca = t.get("created_at")
    out["created_at"] = ca.isoformat() if hasattr(ca, "isoformat") else ca
    idate = t.get("intended_start_date")
    out["intended_start_date"] = idate.isoformat() if hasattr(idate, "isoformat") else (idate if idate else None)
    return out


def _populate_session_cache(user):
    """Store user, friends, gear, and trips in session (call on login/signup)."""
    uid = user["id"]
    session["user"] = {"id": user["id"], "username": user["username"]}
    session["user_id"] = uid
    session["gear"] = _serialize_gear(list_gear(uid))
    session["friends"] = [{"id": f["id"], "username": f["username"]} for f in list_friends(uid)]
    session["trips"] = [_serialize_trip(t) for t in list_trips_for_user(uid)]


def refresh_session_cache(user_id):
    """Refresh session cache for gear, friends, and trips (call after mutations)."""
    session["gear"] = _serialize_gear(list_gear(user_id))
    session["friends"] = [{"id": f["id"], "username": f["username"]} for f in list_friends(user_id)]
    session["trips"] = [_serialize_trip(t) for t in list_trips_for_user(user_id)]


def require_auth():
    """Return current user dict (id, username) from session cache or DB, or None."""
    cached = session.get("user")
    if cached and "id" in cached and "username" in cached:
        return cached
    uid = session.get("user_id")
    if not uid:
        return None
    user = get_user_by_id(uid)
    if user:
        session["user"] = {"id": user["id"], "username": user["username"]}
    return user


# ----------------------
# SIGNUP
# ----------------------
@app.post("/api/signup")
def signup():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify(error="Missing username or password"), 400

    if user_exists_by_username(username):
        return jsonify(error="Username already exists"), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = create_user(username, pw_hash)

    session["user_id"] = user["id"]
    session.permanent = True
    _populate_session_cache(user)

    return jsonify(
        ok=True,
        user={"id": user["id"], "username": user["username"]}
    )


# ----------------------
# LOGIN
# ----------------------
@app.post("/api/login")
def login_route():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify(error="Missing username or password"), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify(error="Invalid credentials"), 401

    if not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    session["user_id"] = user["id"]
    session.permanent = True
    _populate_session_cache({"id": user["id"], "username": user["username"]})

    return jsonify(ok=True)


# ----------------------
# LOGOUT
# ----------------------
@app.post("/api/logout")
def logout_route():
    session.clear()
    return jsonify(ok=True)


# ----------------------
# CURRENT USER
# ----------------------
@app.get("/api/me")
def me():
    user = require_auth()
    if not user:
        return jsonify(error="Not logged in"), 401

    return jsonify(
        id=user["id"],
        username=user["username"]
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
