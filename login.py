import os
from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from datetime import timedelta

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

# --- Fake In-Memory "DB" ---
users_by_username = {}  # username -> user dict
users_by_id = {}        # id -> user dict
next_id = 1


def require_auth():
    uid = session.get("user_id")
    if not uid or uid not in users_by_id:
        return None
    return users_by_id[uid]


# ----------------------
# SIGNUP
# ----------------------
@app.post("/api/signup")
def signup():
    global next_id
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify(error="Missing username or password"), 400

    if username in users_by_username:
        return jsonify(error="Username already exists"), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = {
        "id": next_id,
        "username": username,
        "pw_hash": pw_hash
    }

    next_id += 1
    users_by_username[username] = user
    users_by_id[user["id"]] = user

    # Auto-login
    session["user_id"] = user["id"]
    session.permanent = True

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

    user = users_by_username.get(username)
    if not user:
        return jsonify(error="Invalid credentials"), 401

    if not bcrypt.check_password_hash(user["pw_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    session["user_id"] = user["id"]
    session.permanent = True

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
