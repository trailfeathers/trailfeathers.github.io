const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

document.addEventListener("DOMContentLoaded", () => {
  // First Page buttons
  const loginButton = document.querySelector("#login");
  const registerButton = document.querySelector("#register");

  if (loginButton) {
    loginButton.addEventListener("click", () => {
      window.location.href = "login.html";
    });
  }

  if (registerButton) {
    registerButton.addEventListener("click", () => {
      window.location.href = "register.html";
    });
  }

  // Login Form
  const loginForm = document.querySelector("#login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const username = document.querySelector("#username").value;
      const password = document.querySelector("#password").value;

      const res = await fetch(`${API_BASE}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok) return alert(data.error || "Login failed");
      window.location.href = "dashboard.html";
    });
  }

  // Registration Form
  const registerForm = document.querySelector("#register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const username = document.querySelector("#username").value;
      const password = document.querySelector("#password").value;
      const confirm = document.querySelector("#confirm-password").value;

      if (password !== confirm) return alert("Passwords do not match");

      const res = await fetch(`${API_BASE}/api/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok) return alert(data.error || "Signup failed");
      window.location.href = "dashboard.html";
    });
  }

  // Dashboard welcome
  const welcomeEl = document.querySelector("#welcome");
  if (welcomeEl) {
    (async () => {
      const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
      if (!res.ok) return (window.location.href = "login.html");
      const user = await res.json();
      welcomeEl.textContent = `Welcome, ${user.username}`;
    })();
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