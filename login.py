from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from datetime import timedelta
import secrets

login = Flask(__name__)
bcrypt = Bcrypt(login)

# Secret key used to sign the session cookie
login.config["SECRET_KEY"] = secrets.token_hex(32)

# Server-side sessions (stores session data on the server; cookie holds only a session id)
login.config["SESSION_TYPE"] = "filesystem"
login.config["SESSION_PERMANENT"] = True
login.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)

# Cookie security settings (set SESSION_COOKIE_SECURE=True in production with HTTPS)
login.config["SESSION_COOKIE_HTTPONLY"] = True
login.config["SESSION_COOKIE_SAMESITE"] = "Lax"
login.config["SESSION_COOKIE_SECURE"] = False

Session(login)

# --- Fake "DB" for demo ---
users_by_email = {}  # email -> {id, email, pw_hash}
users_by_username = {}  # username -> user
users_by_id = {}     # id -> user dict
next_id = 1

def require_auth():
  """Helper for protected routes."""
  uid = session.get("user_id")
  if not uid or uid not in users_by_id:
    return None
  return users_by_id[uid]

@login.post("/api/signup")
def signup():
    global next_id
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(error="Missing email or password"), 400

    if email in users_by_email:
        return jsonify(error="Email already exists"), 409
    
    if username in users_by_username:
        return jsonify(error="Username already exists"), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = {"id": next_id, "email": email, "pw_hash": pw_hash}
    next_id += 1

    users_by_email[email] = user
    users_by_id[user["id"]] = user

  # Auto-login after signup
    session["user_id"] = user["id"]
    session.permanent = True

    return jsonify(ok=True, user={"id": user["id"], "email": user["email"], "username": user["username"]})

@login.post("/api/login")
def login():
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

@login.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

@login.get("/api/me")
def me():
    user = require_auth()
    if not user:
        return jsonify(error="Not logged in"), 401
    return jsonify(id=user["id"], email=user["email"], username=user["username"])

if __name__ == "__main__":
    login.run(debug=True, port=5000)
