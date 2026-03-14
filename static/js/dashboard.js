/**
 * First page and dashboard navigation (buttons, banner welcome).
 *
 * Runs on index.html (first page) and dashboard.html. Wires: first-page Login/Register buttons,
 * dashboard buttons (inventory, plan trip, add friend, home), and banner "Welcome, {username}"
 * on the dashboard only (via /api/me).
 */
import { API_BASE } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
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

  // Dashboard buttons
  const inventory = document.querySelector("#inventory");
  if (inventory) inventory.addEventListener("click", () => (window.location.href = "inventory.html"));
  const planTrip = document.querySelector("#plan-trip");
  if (planTrip) planTrip.addEventListener("click", () => (window.location.href = "trip.html"));
  const addFriend = document.querySelector("#add-friend");
  if (addFriend) addFriend.addEventListener("click", () => (window.location.href = "social_center/friends.html"));
  const home = document.querySelector("#home");
  if (home) home.addEventListener("click", () => (window.location.href = "dashboard.html"));

  /* Banner: show "Welcome, {username}" only on dashboard (path ends with dashboard.html and not trip_dashboard). */
  const bannerTitleEl = document.querySelector("#banner-title");
  const path = (window.location.pathname || "").toLowerCase();
  const isDashboard = path.endsWith("dashboard.html") && !path.includes("trip_dashboard");
  if (bannerTitleEl && isDashboard) {
    (async () => {
      try {
        const res = await fetch(API_BASE + "/api/me", { credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          if (data.username) bannerTitleEl.textContent = "Welcome, " + data.username;
        }
      } catch (_) {}
    })();
  }
});
