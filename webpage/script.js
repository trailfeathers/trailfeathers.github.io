// First Page
const loginButton = document.querySelector("#login");
const registerButton = document.querySelector("#register");

if (loginButton) {
  loginButton.addEventListener("click", () => {
    window.location.href = "webpage/login.html";
  });
}

if (registerButton) {
  registerButton.addEventListener("click", () => {
    window.location.href = "webpage/register.html";
  });
}

// Login Page
const loginForm = document.querySelector("#login-form");

if (loginForm) {
  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    window.location.href = "dashboard.html";
  });
}

// Registration Page
const registerForm = document.querySelector("#register-form");

if (registerForm) {
  registerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    window.location.href = "dashboard.html";
  });
}

// Dashboard
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