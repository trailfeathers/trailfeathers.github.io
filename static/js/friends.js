/**
 * TrailFeathers - Friends page: requests, friends list, add friend form, favorites section.
 * Group: TrailFeathers
 * Authors: Kim, Smith, Domst, and Snider
 * Last updated: 3/13/26
 *
 * Runs on friends page (e.g. social_center/friends.html if using main.js).
 * Loads incoming friend requests (/api/friends/requests), friends list (/api/friends), and
 * favorites; supports accept/decline, add-friend search, and favorite-hike display. Note: the
 * Social Center friends.html may use social_center_friends.js instead of this module.
 */
import { API_BASE } from "./config.js";
import { escapeHtml } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const addFriendForm = document.querySelector("#add-friend-form");
  const friendRequestsList = document.querySelector("#friend-requests-list");
  const myFriendsList = document.querySelector("#my-friends-list");

  /** Fetches pending requests and renders Accept/Decline buttons with handlers. */
  async function loadFriendRequests() {
    if (!friendRequestsList) return;
    try {
      const res = await fetch(API_BASE + "/api/friends/requests", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        friendRequestsList.innerHTML = "<p>Could not load requests.</p>";
        return;
      }
      const requests = await res.json();
      if (requests.length === 0) {
        friendRequestsList.innerHTML = "<p>No pending requests.</p>";
        return;
      }
      friendRequestsList.innerHTML = requests
        .map(
          (r) =>
            `<div class="friend-request-item" data-request-id="${r.id}">
              <span>${escapeHtml(r.sender_username)}</span>
              <button type="button" class="accept-request" data-request-id="${r.id}">Accept</button>
              <button type="button" class="decline-request" data-request-id="${r.id}">Decline</button>
            </div>`
        )
        .join("");
      friendRequestsList.querySelectorAll(".accept-request").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-request-id");
          try {
            const r = await fetch(API_BASE + "/api/friends/requests/" + id + "/accept", {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
            });
            if (r.ok) {
              loadFriendRequests();
              if (myFriendsList) loadMyFriends();
            }
          } catch (_) {}
        });
      });
      friendRequestsList.querySelectorAll(".decline-request").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-request-id");
          try {
            const r = await fetch(API_BASE + "/api/friends/requests/" + id + "/decline", {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
            });
            if (r.ok) loadFriendRequests();
          } catch (_) {}
        });
      });
    } catch (_) {
      friendRequestsList.innerHTML = "<p>Could not load requests.</p>";
    }
  }

  /** Fetches friends list and renders. */
  async function loadMyFriends() {
    if (!myFriendsList) return;
    try {
      const res = await fetch(API_BASE + "/api/friends", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        myFriendsList.innerHTML = "<p>Could not load friends.</p>";
        return;
      }
      const friends = await res.json();
      if (friends.length === 0) {
        myFriendsList.innerHTML = "<p>No friends yet.</p>";
        return;
      }
      myFriendsList.innerHTML = friends
        .map((f) => `<div class="friend-item">${escapeHtml(f.username)}</div>`)
        .join("");
    } catch (_) {
      myFriendsList.innerHTML = "<p>Could not load friends.</p>";
    }
  }

  if (friendRequestsList) loadFriendRequests();
  if (myFriendsList) loadMyFriends();

  if (addFriendForm) {
    addFriendForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = document.querySelector("#add-friend-error");
      const successEl = document.querySelector("#add-friend-success");
      if (errEl) errEl.textContent = "";
      if (successEl) successEl.textContent = "";
      const username = document.querySelector("#friend-username").value.trim();
      if (!username) {
        if (errEl) errEl.textContent = "Enter a username.";
        return;
      }
      try {
        const res = await fetch(API_BASE + "/api/friends/request", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username }),
        });
        if (res.ok) {
          if (successEl) successEl.textContent = "Request sent.";
          addFriendForm.reset();
          if (friendRequestsList) loadFriendRequests();
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Could not send request.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  // My favorite hikes
  const myFavoritesList = document.querySelector("#my-favorites-list");
  const addFavoriteSelect = document.querySelector("#add-favorite-select");
  const addFavoriteBtn = document.querySelector("#add-favorite-btn");

  async function loadMyFavorites() {
    if (!myFavoritesList) return;
    try {
      const res = await fetch(API_BASE + "/api/me/favorites", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        myFavoritesList.innerHTML = "<p>Could not load favorites.</p>";
        return;
      }
      const favorites = await res.json();
      if (favorites.length === 0) {
        myFavoritesList.innerHTML = "<p>No favorite hikes yet. Add some from the catalog above.</p>";
        return;
      }
      myFavoritesList.innerHTML = favorites
        .map(
          (f) =>
            `<div class="favorite-hike-item" data-id="${f.id}">
              <div class="favorite-hike-info">
                <strong>${escapeHtml(f.hike_name)}</strong>
                ${f.distance || f.elevation_gain ? `<span class="favorite-hike-meta">${[f.distance, f.elevation_gain].filter(Boolean).join(" · ")}</span>` : ""}
                ${f.source_url ? `<a href="${escapeHtml(f.source_url)}" target="_blank" rel="noopener" class="favorite-hike-link">Source</a>` : ""}
              </div>
              <button type="button" class="remove-favorite secondary" data-id="${f.id}">Remove</button>
            </div>`
        )
        .join("");
      myFavoritesList.querySelectorAll(".remove-favorite").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = parseInt(btn.getAttribute("data-id"), 10);
          try {
            const r = await fetch(API_BASE + "/api/me/favorites/" + id, {
              method: "DELETE",
              credentials: "include",
            });
            if (r.ok) {
              loadMyFavorites();
              loadLocationsForFavorites();
            }
          } catch (_) {}
        });
      });
    } catch (_) {
      myFavoritesList.innerHTML = "<p>Could not load favorites.</p>";
    }
  }

  async function loadLocationsForFavorites() {
    if (!addFavoriteSelect) return;
    try {
      const [locRes, favRes] = await Promise.all([
        fetch(API_BASE + "/api/locations", { credentials: "include" }),
        fetch(API_BASE + "/api/me/favorites", { credentials: "include" }),
      ]);
      if (!locRes.ok || !favRes.ok) return;
      const locations = await locRes.json();
      const favorites = await favRes.json();
      const favoritedIds = new Set(favorites.map((f) => f.id));
      const options = locations.filter((loc) => !favoritedIds.has(loc.id));
      addFavoriteSelect.innerHTML =
        '<option value="">Choose a hike…</option>' +
        options
          .map(
            (loc) =>
              `<option value="${loc.id}">${escapeHtml(loc.hike_name || "Unnamed")}${loc.distance ? " — " + loc.distance : ""}</option>`
          )
          .join("");
    } catch (_) {}
  }

  if (myFavoritesList) loadMyFavorites();
  if (addFavoriteSelect) loadLocationsForFavorites();

  if (addFavoriteBtn && addFavoriteSelect) {
    addFavoriteBtn.addEventListener("click", async () => {
      const errEl = document.querySelector("#add-favorite-error");
      if (errEl) errEl.textContent = "";
      const id = addFavoriteSelect.value;
      if (!id) {
        if (errEl) errEl.textContent = "Choose a hike from the list.";
        return;
      }
      try {
        const res = await fetch(API_BASE + "/api/me/favorites", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ trip_report_info_id: parseInt(id, 10) }),
        });
        if (res.ok) {
          loadMyFavorites();
          loadLocationsForFavorites();
          addFavoriteSelect.value = "";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Could not add favorite.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }
});
