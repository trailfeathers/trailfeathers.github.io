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
    loginForm.addEventListener("submit", () => {
      event.preventDefault();
      window.location.href = "dashboard.html";
    });
  }

  // Registration Form
  const registerForm = document.querySelector("#register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", () => {
      event.preventDefault();
      window.location.href = "dashboard.html";
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