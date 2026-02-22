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

  // Back button (Login Page)
  const backButtonLogin = document.querySelector("#back-button-login");
  if (backButtonLogin) {
    backButtonLogin.addEventListener("click", () => {
      window.history.back();
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

  // Back button (Registration Page)
  const backButtonRegister = document.querySelector("#back-button-register");
  if (backButtonRegister) {
    backButtonRegister.addEventListener("click", () => {
      window.history.back();
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

  // ---------- Inventory: load gear and add form ----------
  const inventoryTable = document.querySelector("#inventory-table");
  const addItemForm = document.querySelector("#add-item-form");

  async function loadGear() {
    if (!inventoryTable) return;
    try {
      const res = await fetch(API_BASE + "/api/gear", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        inventoryTable.innerHTML = "<tr><td colspan=\"7\">Could not load gear.</td></tr>";
        return;
      }
      const items = await res.json();
      if (items.length === 0) {
        inventoryTable.innerHTML = "<tr><td colspan=\"7\">No gear yet. Add some below.</td></tr>";
        return;
      }
      inventoryTable.innerHTML = items
        .map(
          (item) =>
            `<tr>
              <td>${escapeHtml(item.type || "—")}</td>
              <td>${escapeHtml(item.name || "—")}</td>
              <td>${escapeHtml(item.capacity != null ? String(item.capacity) : "—")}</td>
              <td>${item.weight_oz != null ? item.weight_oz : "—"}</td>
              <td>${escapeHtml(item.brand || "—")}</td>
              <td>${escapeHtml(item.condition || "—")}</td>
              <td>${escapeHtml(item.notes || "—")}</td>
            </tr>`
        )
        .join("");
    } catch (_) {
      inventoryTable.innerHTML = "<tr><td colspan=\"7\">Could not load gear.</td></tr>";
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  if (inventoryTable) loadGear();

  // ---------- Friends page: load requests and friends, add-friend form, accept/decline ----------
  const addFriendForm = document.querySelector("#add-friend-form");
  const friendRequestsList = document.querySelector("#friend-requests-list");
  const myFriendsList = document.querySelector("#my-friends-list");

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

  // ---------- Trip list and create trip ----------
  const tripList = document.querySelector("#trip-list");
  const createTripForm = document.querySelector("#create-trip-form");

  async function loadTrips() {
    if (!tripList) return;
    try {
      const res = await fetch(API_BASE + "/api/trips", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        tripList.innerHTML = "<p>Could not load trips.</p>";
        return;
      }
      const trips = await res.json();
      if (trips.length === 0) {
        tripList.innerHTML = "<p>No trips yet. Create one below.</p>";
        return;
      }
      tripList.innerHTML = trips
        .map(
          (t) =>
            `<div class="trip-card trip-card-clickable" data-trip-id="${t.id}">
              <h3>${escapeHtml(t.trip_name || "Unnamed")}</h3>
              <p><strong>Trail:</strong> ${escapeHtml(t.trail_name || "—")}</p>
              <p><strong>Activity:</strong> ${escapeHtml(t.activity_type || "—")}</p>
              <p><strong>Start:</strong> ${t.intended_start_date ? escapeHtml(String(t.intended_start_date).slice(0, 10)) : "—"}</p>
              <p><strong>Created by:</strong> ${escapeHtml(t.creator_username || "—")}</p>
            </div>`
        )
        .join("");
      tripList.querySelectorAll(".trip-card-clickable").forEach((el) => {
        el.addEventListener("click", () => {
          const id = el.getAttribute("data-trip-id");
          window.location.href = "trip_dashboard.html?id=" + encodeURIComponent(id);
        });
      });
    } catch (_) {
      tripList.innerHTML = "<p>Could not load trips.</p>";
    }
  }

  if (tripList) loadTrips();

  async function loadTripInvites() {
    const section = document.querySelector("#trip-invites-section");
    const listEl = document.querySelector("#trip-invites-list");
    if (!section || !listEl) return;
    try {
      const res = await fetch(API_BASE + "/api/trip-invites", { credentials: "include" });
      if (res.status === 401) return;
      if (!res.ok) return;
      const invites = await res.json();
      if (invites.length === 0) return;
      section.style.display = "block";
      listEl.innerHTML = invites
        .map(
          (inv) =>
            `<div class="trip-invite-item" data-invite-id="${inv.id}">
              <p><strong>${escapeHtml(inv.trip_name)}</strong> — ${escapeHtml(inv.inviter_username)} invited you.</p>
              <a href="trip_dashboard.html?id=${encodeURIComponent(inv.trip_id)}">View trip</a>
              <button type="button" class="trip-invite-accept" data-invite-id="${inv.id}">Accept</button>
              <button type="button" class="trip-invite-decline" data-invite-id="${inv.id}">Decline</button>
            </div>`
        )
        .join("");
      listEl.querySelectorAll(".trip-invite-accept").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-invite-id");
          const r = await fetch(API_BASE + "/api/trip-invites/" + id + "/accept", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          });
          if (r.ok) {
            loadTripInvites();
            if (tripList) loadTrips();
          }
        });
      });
      listEl.querySelectorAll(".trip-invite-decline").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-invite-id");
          const r = await fetch(API_BASE + "/api/trip-invites/" + id + "/decline", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          });
          if (r.ok) loadTripInvites();
        });
      });
    } catch (_) {}
  }
  loadTripInvites();

  if (createTripForm) {
    createTripForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = document.querySelector("#create-trip-error");
      if (errEl) errEl.textContent = "";
      const trip_name = document.querySelector("#trip-name").value.trim();
      if (!trip_name) {
        if (errEl) errEl.textContent = "Trip name is required.";
        return;
      }
      const payload = {
        trip_name,
        trail_name: document.querySelector("#trip-trail").value.trim() || undefined,
        activity_type: document.querySelector("#trip-activity").value.trim() || undefined,
        intended_start_date: document.querySelector("#trip-date").value || undefined,
      };
      try {
        const res = await fetch(API_BASE + "/api/trips", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          createTripForm.reset();
          loadTrips();
          if (errEl) errEl.textContent = "";
          if (data.id) window.location.href = "trip_dashboard.html?id=" + encodeURIComponent(data.id);
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Could not create trip.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  // ---------- Trip dashboard (trip_dashboard.html?id=...) ----------
  const tripDashboardContent = document.querySelector("#trip-dashboard-content");
  const tripDashboardLoading = document.querySelector("#trip-dashboard-loading");
  const params = new URLSearchParams(window.location.search);
  const tripIdParam = params.get("id");

  if (tripDashboardContent && tripIdParam) {
    (async () => {
      try {
        const res = await fetch(API_BASE + "/api/trips/" + tripIdParam, { credentials: "include" });
        if (res.status === 401) {
          window.location.href = "login.html";
          return;
        }
        if (res.status === 404 || !res.ok) {
          tripDashboardLoading.remove();
          tripDashboardContent.innerHTML = "<p>Trip not found.</p>";
          return;
        }
        const trip = await res.json();
        document.querySelector(".banner h1").textContent = trip.trip_name || "Trip";
        tripDashboardLoading.remove();
        tripDashboardContent.innerHTML =
          `<h2>${escapeHtml(trip.trip_name || "Trip")}</h2>
           <p><strong>Trail:</strong> ${escapeHtml(trip.trail_name || "—")}</p>
           <p><strong>Activity:</strong> ${escapeHtml(trip.activity_type || "—")}</p>
           <p><strong>Start date:</strong> ${trip.intended_start_date ? escapeHtml(String(trip.intended_start_date).slice(0, 10)) : "—"}</p>
           <p><strong>Created by:</strong> ${escapeHtml(trip.creator_username || "—")}</p>`;

        const invitesRes = await fetch(API_BASE + "/api/trip-invites", { credentials: "include" });
        const myInvites = invitesRes.ok ? await invitesRes.json() : [];
        const pendingInvite = myInvites.find((inv) => String(inv.trip_id) === String(tripIdParam));

        if (pendingInvite) {
          const invitedSection = document.querySelector("#trip-dashboard-invited");
          if (invitedSection) {
            invitedSection.style.display = "block";
            const msg = document.querySelector("#trip-invited-message");
            if (msg) msg.textContent = "You've been invited to this trip. Accept to join.";
            const acceptBtn = document.querySelector("#trip-invite-accept");
            const declineBtn = document.querySelector("#trip-invite-decline");
            if (acceptBtn) {
              acceptBtn.onclick = async () => {
                const r = await fetch(API_BASE + "/api/trip-invites/" + pendingInvite.id + "/accept", {
                  method: "POST",
                  credentials: "include",
                  headers: { "Content-Type": "application/json" },
                });
                if (r.ok) window.location.reload();
              };
            }
            if (declineBtn) {
              declineBtn.onclick = async () => {
                const r = await fetch(API_BASE + "/api/trip-invites/" + pendingInvite.id + "/decline", {
                  method: "POST",
                  credentials: "include",
                  headers: { "Content-Type": "application/json" },
                });
                if (r.ok) window.location.href = "trip.html";
              };
            }
          }
        } else {
          const collabRes = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/collaborators", { credentials: "include" });
          const collaborators = collabRes.ok ? await collabRes.json() : [];
          let pendingInvitesList = [];
          let friendsToShow = [];
          if (trip.is_creator) {
            const invitesListRes = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/invites", { credentials: "include" });
            const friendsRes = await fetch(API_BASE + "/api/friends", { credentials: "include" });
            pendingInvitesList = invitesListRes.ok ? await invitesListRes.json() : [];
            const friends = friendsRes.ok ? await friendsRes.json() : [];
            const collabIds = new Set(collaborators.map((c) => c.id));
            const pendingInviteeIds = new Set(pendingInvitesList.map((p) => p.invitee_id));
            friendsToShow = friends.filter((f) => !collabIds.has(f.id) && !pendingInviteeIds.has(f.id));
          }

          const membersSection = document.querySelector("#trip-dashboard-members");
          if (membersSection) {
            membersSection.style.display = "block";
            const listEl = document.querySelector("#trip-collaborators-list");
            if (listEl) {
              listEl.innerHTML = collaborators.length
                ? collaborators.map((c) => `<p>${escapeHtml(c.username)} <span class="role-badge">${escapeHtml(c.role)}</span></p>`).join("")
                : "<p>No members yet.</p>";
            }
          }

          if (trip.is_creator) {
            const pendingSection = document.querySelector("#trip-dashboard-pending-invites");
            if (pendingSection && pendingInvitesList.length > 0) {
              pendingSection.style.display = "block";
              const listEl = document.querySelector("#trip-pending-invites-list");
              if (listEl) listEl.innerHTML = pendingInvitesList.map((p) => `<p>${escapeHtml(p.invitee_username)} (pending)</p>`).join("");
            }

            const inviteSection = document.querySelector("#trip-dashboard-invite-friend");
            if (inviteSection) {
              inviteSection.style.display = "block";
              const selectEl = document.querySelector("#trip-invite-friend-select");
              const errEl = document.querySelector("#trip-invite-error");
              if (selectEl) {
                selectEl.innerHTML = "<option value=\"\">Choose a friend…</option>" +
                  friendsToShow.map((f) => `<option value="${f.id}">${escapeHtml(f.username)}</option>`).join("");
              }
              const inviteBtn = document.querySelector("#trip-invite-friend-btn");
              if (inviteBtn && selectEl) {
                inviteBtn.onclick = async () => {
                  const friendId = selectEl.value;
                  if (!friendId) return;
                  if (errEl) errEl.textContent = "";
                  try {
                    const r = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/invites", {
                      method: "POST",
                      credentials: "include",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ user_id: parseInt(friendId, 10) }),
                    });
                    if (r.ok) {
                      window.location.reload();
                      return;
                    }
                    const data = await r.json().catch(() => ({}));
                    if (errEl) errEl.textContent = data.error || "Could not send invite.";
                  } catch (_) {
                    if (errEl) errEl.textContent = "Could not reach the server.";
                  }
                };
              }
            }
          }
        }
      } catch (_) {
        tripDashboardLoading.remove();
        tripDashboardContent.innerHTML = "<p>Could not load trip.</p>";
      }
    })();
  } else if (tripDashboardContent && !tripIdParam) {
    tripDashboardLoading.remove();
    tripDashboardContent.innerHTML = "<p>No trip selected. <a href=\"trip.html\">Back to trips</a></p>";
  }

  if (addItemForm) {
    addItemForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = document.querySelector("#add-gear-error");
      if (errEl) errEl.textContent = "";

      const name = document.querySelector("#gear-name").value.trim();
      if (!name) {
        if (errEl) errEl.textContent = "Name is required.";
        return;
      }

      const payload = {
        type: (document.querySelector("#gear-type").value || "other").trim() || "other",
        name,
        capacity: document.querySelector("#gear-capacity").value.trim() || undefined,
        brand: document.querySelector("#gear-brand").value.trim() || undefined,
        condition: document.querySelector("#gear-condition").value.trim() || undefined,
        notes: document.querySelector("#gear-notes").value.trim() || undefined,
      };
      const weightVal = document.querySelector("#gear-weight").value;
      if (weightVal !== "" && weightVal != null) {
        const w = parseFloat(weightVal);
        if (!Number.isNaN(w) && w >= 0) payload.weight_oz = w;
      }

      try {
        const res = await fetch(API_BASE + "/api/gear", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addItemForm.reset();
          document.querySelector("#gear-type").value = "other";
          loadGear();
          if (errEl) errEl.textContent = "";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Could not add gear.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }
});

// Inventory nav (when already on page)
const home = document.querySelector("#home");
if (home) {
  home.addEventListener("click", () => {
    window.location.href = "dashboard.html";
  });
}

// Trip Planner