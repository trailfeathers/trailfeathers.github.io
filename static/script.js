const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

document.addEventListener("DOMContentLoaded", () => {
  // First Page buttons
  const loginButton = document.querySelector("#login");
  const registerButton = document.querySelector("#register");

  if (loginButton) {
    loginButton.addEventListener("click", () => {
      window.location.href = "static/login.html";
    });
  }

  if (registerButton) {
    registerButton.addEventListener("click", () => {
      window.location.href = "static/register.html";
    });
  }

  // Login Form – call API, then redirect or show error
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

  // Registration Form – validate confirm password, call API, then redirect or show error
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
        if (res.status === 201) {
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

  // Dashboard buttons
  const inventory = document.querySelector("#inventory");
  if (inventory) inventory.addEventListener("click", () => (window.location.href = "inventory.html"));
  const planTrip = document.querySelector("#plan-trip");
  if (planTrip) planTrip.addEventListener("click", () => (window.location.href = "trip.html"));
  const addFriend = document.querySelector("#add-friend");
  if (addFriend) addFriend.addEventListener("click", () => (window.location.href = "friends.html"));
  const home = document.querySelector("#home");
  if (home) home.addEventListener("click", () => (window.location.href = "dashboard.html"));
});


// Inventory
const home = document.querySelector("#home");

if (home) {
    home.addEventListener("click", () => {
      window.location.href = "dashboard.html";
    });
}

// Trip Planner

// Friends