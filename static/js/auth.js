/**
 * Login, register, and logout handlers.
 *
 * Runs on login.html and register.html. Handles: login form (POST /api/login, redirect to dashboard),
 * register form (confirm password, POST /api/signup, 409 → "Username already exists"), back buttons,
 * and logout button (POST /api/logout, then redirect to login) on any page that includes it.
 */
import { API_BASE } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
  const backButtonLogin = document.querySelector("#back-button-login");
  if (backButtonLogin) {
    backButtonLogin.addEventListener("click", () => {
      window.location.href = "register.html";
    });
  }

  const loginForm = document.querySelector("#login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.querySelector("#login-form #username").value.trim();
      const password = document.querySelector("#login-form #password").value;
      const errEl = document.querySelector("#login-error");
      if (errEl) errEl.textContent = "";

      if (!username || !password) {
        if (errEl) errEl.textContent = "Please enter username and password.";
        return;
      }

      try {
        const res = await fetch(API_BASE + "/api/login", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        if (res.ok) {
          window.location.href = "dashboard.html";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Invalid credentials.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  const registerForm = document.querySelector("#register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.querySelector("#register-form #username").value.trim();
      const password = document.querySelector("#register-form #password").value;
      const confirmPassword = document.querySelector("#register-form #confirm-password").value;
      const errEl = document.querySelector("#register-error");
      if (errEl) errEl.textContent = "";

      if (!username || !password) {
        if (errEl) errEl.textContent = "Please enter username and password.";
        return;
      }
      if (password !== confirmPassword) {
        if (errEl) errEl.textContent = "Passwords don't match.";
        return;
      }

      try {
        const res = await fetch(API_BASE + "/api/signup", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        if (res.ok) {
          window.location.href = "dashboard.html";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) {
          if (errEl) errEl.textContent = "Username already exists.";
        } else {
          if (errEl) errEl.textContent = data.error || "Something went wrong. Try again.";
        }
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  const backButtonRegister = document.querySelector("#back-button-register");
  if (backButtonRegister) {
    backButtonRegister.addEventListener("click", () => {
      window.location.href = "login.html";
    });
  }

  const logoutBtn = document.querySelector("#logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        const res = await fetch(API_BASE + "/api/logout", {
          method: "POST",
          credentials: "include"
        });
        if (res.ok) {
          window.location.href = "login.html";
        }
      } catch (err) {
        console.error("Logout failed:", err);
        window.location.href = "login.html";
      }
    });
  }
});
