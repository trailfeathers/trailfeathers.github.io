const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

// First Page
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

// Login
const loginForm = document.querySelector("#login-form");

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;

    const res = await fetch(`${API_BASE}/api/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include", // 🔑 session cookies
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Login failed");
      return;
    }

    window.location.href = "dashboard.html";
  });
}


// Registration Page
const registerForm = document.querySelector("#register-form");

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;
    const confirm = document.querySelector("#confirm-password").value;

    if (password !== confirm) {
      alert("Passwords do not match");
      return;
    }

    const res = await fetch(`${API_BASE}/api/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Signup failed");
      return;
    }

    window.location.href = "dashboard.html";
  });
}


// Dashboard
const welcomeEl = document.querySelector("#welcome");
if (welcomeEl) {
  (async () => {
    const res = await fetch(`${API_BASE}/api/me`, {
      credentials: "include"
    });

    if (!res.ok) {
      window.location.href = "login.html";
      return;
    }

    const user = await res.json();
    welcomeEl.textContent = `Welcome, ${user.username}`;
  })();
}


const inventory = document.querySelector("#inventory");
const planTrip = document.querySelector("#plan-trip");
const addFriend = document.querySelector("#add-friend");

if (inventory) {
    inventory.addEventListener("click", () => {
      window.location.href = "inventory.html";
    });
}
if (planTrip) {
    planTrip.addEventListener("click", () => {
      window.location.href = "trip.html";
    });
}
if (addFriend) {
    addFriend.addEventListener("click", () => {
      window.location.href = "friends.html";
    });
}

// Inventory
const home = document.querySelector("#home");

if (home) {
    home.addEventListener("click", () => {
      window.location.href = "dashboard.html";
    });
}

// Trip Planner

// Friends