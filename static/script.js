const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

// Gear library: map requirement_type key → category for dashboard grouping (client-side only)
const REQUIREMENT_KEY_TO_CATEGORY = {
  shelter: "Sleep Systems",
  sleeping_bag: "Sleep Systems",
  sleeping_pad: "Sleep Systems",
  emergency_shelter: "Sleep Systems",
  water_filter: "Food & Water",
  stove: "Food & Water",
  cookware: "Food & Water",
  water_capacity: "Food & Water",
  snacks_food: "Food & Water",
  cooler: "Food & Water",
  lantern: "Food & Water",
  backpack: "Packs",
  daypack: "Packs",
  first_aid: "Safety & First Aid",
  headlamp: "Safety & First Aid",
  navigation: "Safety & First Aid",
  rain_gear: "Safety & First Aid",
  sun_protection: "Safety & First Aid",
  beacon: "Safety & First Aid",
  avalanche_gear: "Safety & First Aid",
  insulation_layer: "Clothing & Layers",
  helmet: "Climbing & Technical",
  harness: "Climbing & Technical",
  rope: "Climbing & Technical",
  binoculars: "Other",
  field_guide: "Other",
  skis: "Other",
  other: "Other"
};
const GEAR_CATEGORY_ORDER = [
  "Sleep Systems",
  "Food & Water",
  "Packs",
  "Safety & First Aid",
  "Clothing & Layers",
  "Climbing & Technical",
  "Other"
];

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
      window.location.href = "register.html";
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
      window.location.href = "login.html";
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

  // ---------- Banner: show "Welcome, {username}" on auth pages ----------
  const bannerTitleEl = document.querySelector("#banner-title");
  if (bannerTitleEl) {
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

  // ---------- Inventory (Gear Library dashboard): load gear by category and add form ----------
  const gearCategoriesEl = document.querySelector("#gear-categories");
  const gearLoadingEl = document.querySelector("#gear-loading");
  const addItemForm = document.querySelector("#add-item-form");

  function getCategoryForKey(key) {
    if (!key) return "Other";
    return REQUIREMENT_KEY_TO_CATEGORY[key] || "Other";
  }

  async function loadGear() {
    if (!gearCategoriesEl) return;
    try {
      if (gearLoadingEl) gearLoadingEl.textContent = "Loading…";
      const res = await fetch(API_BASE + "/api/gear", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        if (gearLoadingEl) gearLoadingEl.remove();
        gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">Could not load gear.</p>";
        return;
      }
      const items = await res.json();
      if (gearLoadingEl) gearLoadingEl.remove();
      if (items.length === 0) {
        gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">No gear yet. Add some in the form on the right.</p>";
        return;
      }
      const byCategory = {};
      for (const item of items) {
        const key = item.requirement_key || null;
        const cat = getCategoryForKey(key);
        if (!byCategory[cat]) byCategory[cat] = [];
        byCategory[cat].push(item);
      }
      const order = GEAR_CATEGORY_ORDER.filter((c) => byCategory[c] && byCategory[c].length > 0);
      const html = order
        .map((category) => {
          const listItems = byCategory[category]
            .map((item) => {
              const typeLabel = item.requirement_display_name || item.type || "—";
              const coversLabel = item.capacity_persons != null ? `${item.capacity_persons} people` : "Group";
              const meta = [item.capacity ? `Capacity: ${escapeHtml(String(item.capacity))}` : null, coversLabel, item.weight_oz != null ? `${item.weight_oz} oz` : null, item.brand ? escapeHtml(item.brand) : null].filter(Boolean).join(" · ");
              return `<li class="gear-category-item"><strong>${escapeHtml(typeLabel)}</strong>: ${escapeHtml(item.name || "—")}${item.condition || item.notes ? ` <span class="gear-meta">${[item.condition, item.notes].filter(Boolean).map(escapeHtml).join(" — ")}</span>` : ""}${meta ? ` <span class="gear-meta">${meta}</span>` : ""}</li>`;
            })
            .join("");
          return `<div class="gear-category-section"><h3>${escapeHtml(category)}</h3><ul>${listItems}</ul></div>`;
        })
        .join("");
      gearCategoriesEl.innerHTML = html;
    } catch (_) {
      if (gearLoadingEl) gearLoadingEl.remove();
      gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">Could not load gear.</p>";
    }
  }

  async function loadRequirementTypes() {
    const selectEl = document.querySelector("#gear-type");
    if (!selectEl) return;
    try {
      const res = await fetch(API_BASE + "/api/requirement-types", { credentials: "include" });
      if (res.status === 401) return;
      if (!res.ok) {
        selectEl.innerHTML = "<option value=\"\">Could not load types</option>";
        return;
      }
      const types = await res.json();
      if (types.length === 0) {
        selectEl.innerHTML = "<option value=\"\">Other (no types in DB yet)</option>";
        return;
      }
      selectEl.innerHTML = types
        .map((t) => `<option value="${t.id}">${escapeHtml(t.display_name)}</option>`)
        .join("");
    } catch (_) {
      selectEl.innerHTML = "<option value=\"\">Could not load types</option>";
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  if (gearCategoriesEl) loadGear();
  if (document.querySelector("#gear-type")) loadRequirementTypes();

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

  // ---------- Location catalog: searchable combobox (must select from list) ----------
  let locationsCatalog = [];
  const locationSearchInput = document.querySelector("#trip-location-search");
  const tripReportInfoIdInput = document.querySelector("#trip-report-info-id");
  const locationListbox = document.querySelector("#trip-location-listbox");
  const locationCombobox = document.querySelector(".location-combobox");

  async function loadLocations() {
    if (!locationSearchInput) return;
    try {
      const res = await fetch(API_BASE + "/api/locations", { credentials: "include" });
      if (res.status === 401) return;
      if (!res.ok) return;
      locationsCatalog = await res.json();
    } catch (_) {
      locationsCatalog = [];
    }
  }

  function filterLocations(query) {
    const q = (query || "").trim().toLowerCase();
    if (!q) return locationsCatalog.slice(0, 50);
    return locationsCatalog.filter((loc) =>
      (loc.hike_name || "").toLowerCase().includes(q)
    ).slice(0, 50);
  }

  function renderLocationOptions(locations) {
    if (!locationListbox) return;
    if (locations.length === 0) {
      locationListbox.innerHTML = "<li role=\"option\" class=\"location-no-results\">No matching trails. Type to search the catalog.</li>";
      return;
    }
    locationListbox.innerHTML = locations.map((loc) => {
      const meta = [loc.distance, loc.elevation_gain, loc.difficulty].filter(Boolean).join(" · ");
      return `<li role="option" data-id="${loc.id}" data-hike-name="${escapeHtml(loc.hike_name || "")}">${escapeHtml(loc.hike_name || "Unnamed")}${meta ? `<div class="location-option-meta">${escapeHtml(meta)}</div>` : ""}</li>`;
    }).join("");
  }

  function openListbox() {
    if (!locationCombobox) return;
    locationCombobox.setAttribute("aria-expanded", "true");
    const query = locationSearchInput ? locationSearchInput.value.trim() : "";
    const filtered = filterLocations(query);
    renderLocationOptions(filtered);
  }

  function closeListbox() {
    if (locationCombobox) locationCombobox.setAttribute("aria-expanded", "false");
  }

  function selectLocation(id, hikeName) {
    if (tripReportInfoIdInput) tripReportInfoIdInput.value = id;
    if (locationSearchInput) locationSearchInput.value = hikeName || "";
    closeListbox();
  }

  function clearLocationSelection() {
    if (tripReportInfoIdInput) tripReportInfoIdInput.value = "";
  }

  if (locationSearchInput && locationListbox) {
    loadLocations();
    locationSearchInput.addEventListener("focus", () => openListbox());
    locationSearchInput.addEventListener("input", () => {
      clearLocationSelection();
      openListbox();
    });
    locationSearchInput.addEventListener("blur", () => {
      setTimeout(closeListbox, 200);
    });
    locationSearchInput.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeListbox();
        locationSearchInput.blur();
      }
    });
    locationListbox.addEventListener("click", (e) => {
      const opt = e.target.closest("[role=option][data-id]");
      if (opt) {
        e.preventDefault();
        selectLocation(opt.getAttribute("data-id"), opt.getAttribute("data-hike-name"));
      }
    });
  }

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
      const trip_report_info_id = tripReportInfoIdInput ? tripReportInfoIdInput.value.trim() : "";
      if (!trip_report_info_id) {
        if (errEl) errEl.textContent = "Please select a location from the catalog (search and click a trail).";
        return;
      }
      const payload = {
        trip_name,
        trip_report_info_id: parseInt(trip_report_info_id, 10),
        activity_type: document.querySelector("#trip-activity").value || undefined,
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
          clearLocationSelection();
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

  function renderTripDashboard(data) {
    const trip = data.trip;
    const pendingInvite = data.pending_invite || null;
    const locationSummary = data.location_summary || null;
    document.querySelector(".banner h1").textContent = trip.trip_name || "Trip";
    let summaryHtml =
      `<h2>${escapeHtml(trip.trip_name || "Trip")}</h2>
       <p><strong>Trail:</strong> ${escapeHtml(trip.trail_name || "—")}</p>
       <p><strong>Activity:</strong> ${escapeHtml(trip.activity_type || "—")}</p>
       <p><strong>Start date:</strong> ${trip.intended_start_date ? escapeHtml(String(trip.intended_start_date).slice(0, 10)) : "—"}</p>
       <p><strong>Created by:</strong> ${escapeHtml(trip.creator_username || "—")}</p>`;
    if (locationSummary && locationSummary.summarized_description) {
      summaryHtml += `<section class="trip-dashboard-location-summary" aria-label="Trail report summary">
         <h3>Trail report summary</h3>
         <div class="trip-dashboard-ai-summary">${escapeHtml(locationSummary.summarized_description).replace(/\n/g, "<br>")}</div>
         ${locationSummary.source_url ? `<p><a href="${escapeHtml(locationSummary.source_url)}" target="_blank" rel="noopener">View source</a></p>` : ""}
       </section>`;
    }
    tripDashboardContent.innerHTML = summaryHtml;

    const invitedSection = document.querySelector("#trip-dashboard-invited");
    const membersSection = document.querySelector("#trip-dashboard-members");
    const pendingSection = document.querySelector("#trip-dashboard-pending-invites");
    const inviteSection = document.querySelector("#trip-dashboard-invite-friend");
    const gearPoolSection = document.querySelector("#trip-dashboard-gear-pool");
    const assignedGearSection = document.querySelector("#trip-dashboard-assigned-gear");
    const checklistSection = document.querySelector("#trip-dashboard-checklist");
    [invitedSection, membersSection, pendingSection, inviteSection, gearPoolSection, assignedGearSection, checklistSection].forEach((el) => {
      if (el) el.style.display = "none";
    });

    if (pendingInvite) {
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
            if (r.ok) loadTripDashboard();
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
      return;
    }

    const collaborators = data.collaborators || [];
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
      const pendingInvitesList = data.pending_invites || [];
      if (pendingSection && pendingInvitesList.length > 0) {
        pendingSection.style.display = "block";
        const listEl = document.querySelector("#trip-pending-invites-list");
        if (listEl) listEl.innerHTML = pendingInvitesList.map((p) => `<p>${escapeHtml(p.invitee_username)} (pending)</p>`).join("");
      }
      const friendsToShow = data.friends || [];
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
              if (r.ok) loadTripDashboard();
              else {
                const resData = await r.json().catch(() => ({}));
                if (errEl) errEl.textContent = resData.error || "Could not send invite.";
              }
            } catch (_) {
              if (errEl) errEl.textContent = "Could not reach the server.";
            }
          };
        }
      }
    }

    const gearPool = data.gear_pool || [];
    const assignedGear = data.assigned_gear || [];
    if (gearPoolSection && assignedGearSection) {
      if (gearPool.length > 0) {
        gearPoolSection.style.display = "block";
        const poolList = document.querySelector("#trip-gear-pool-list");
        const byOwner = {};
        gearPool.forEach((item) => {
          if (!byOwner[item.owner_username]) byOwner[item.owner_username] = [];
          byOwner[item.owner_username].push(item);
        });
        poolList.innerHTML = Object.keys(byOwner).sort().map((owner) => {
          const items = byOwner[owner];
          return `<div class="gear-owner-section">
            <h4>${escapeHtml(owner)}'s Gear</h4>
            <ul class="gear-pool-items">
              ${items.map((item) => {
                const isAssigned = item.is_assigned;
                const typeLabel = item.requirement_display_name || item.type;
                const coversLabel = item.capacity_persons != null ? `covers ${item.capacity_persons} people` : "group";
                return `<li class="gear-pool-item ${isAssigned ? "assigned" : ""}">
                  <span class="gear-info">
                    <strong>${escapeHtml(typeLabel)}</strong>: ${escapeHtml(item.name)}
                    ${item.capacity ? ` (${escapeHtml(item.capacity)})` : ""} — <em>${coversLabel}</em>
                    ${item.brand ? ` — ${escapeHtml(item.brand)}` : ""}
                  </span>
                  ${isAssigned
                    ? `<button type="button" class="btn-small btn-remove-gear" data-gear-id="${item.id}">Remove</button>`
                    : `<button type="button" class="btn-small btn-add-gear" data-gear-id="${item.id}">Add to Trip</button>`
                  }
                </li>`;
              }).join("")}
            </ul>
          </div>`;
        }).join("");
        poolList.querySelectorAll(".btn-add-gear").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const gearId = btn.getAttribute("data-gear-id");
            try {
              const r = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/gear/" + gearId, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
              });
              if (r.ok) loadTripDashboard();
            } catch (_) {}
          });
        });
        poolList.querySelectorAll(".btn-remove-gear").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const gearId = btn.getAttribute("data-gear-id");
            try {
              const r = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/gear/" + gearId, {
                method: "DELETE",
                credentials: "include",
              });
              if (r.ok) loadTripDashboard();
            } catch (_) {}
          });
        });
      }
      if (assignedGear.length > 0) {
        assignedGearSection.style.display = "block";
        const assignedList = document.querySelector("#trip-assigned-gear-list");
        assignedList.innerHTML = `<ul class="assigned-gear-list">
          ${assignedGear.map((item) => {
            const typeLabel = item.requirement_display_name || item.type;
            const coversLabel = item.capacity_persons != null ? `covers ${item.capacity_persons} people` : "group";
            return `<li>
              <strong>${escapeHtml(typeLabel)}</strong>: ${escapeHtml(item.name)}
              ${item.capacity ? ` (${escapeHtml(item.capacity)})` : ""} — <em>${coversLabel}</em>
              — <em>Owned by ${escapeHtml(item.owner_username)}</em>
            </li>`;
          }).join("")}
        </ul>`;
      }
    }

    const checklist = data.checklist || [];
    if (checklistSection && checklist.length > 0) {
      const checklistList = document.querySelector("#trip-checklist-list");
      checklistList.innerHTML = checklist.map((item) => {
        const name = escapeHtml(item.requirement_display_name || item.requirement_key || "Item");
        let ruleText = "";
        if (item.rule === "per_group") ruleText = "1 per group";
        else if (item.rule === "per_person") ruleText = "1 per person";
        else if (item.rule === "per_N_persons" && item.n_persons) ruleText = `1 per ${item.n_persons} people`;
        const statusClass = item.status === "met" ? "checklist-met" : "checklist-short";
        return `<li class="checklist-item ${statusClass}">
          <strong>${name}</strong>: ${item.required_count} needed${ruleText ? ` (${ruleText})` : ""} — ${item.covered_count} covered <span class="checklist-status">(${item.status})</span>
        </li>`;
      }).join("");
      checklistSection.style.display = "block";
    }
  }

  async function loadTripDashboard() {
    if (!tripDashboardContent || !tripIdParam) return;
    try {
      const res = await fetch(API_BASE + "/api/trips/" + tripIdParam + "/dashboard", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (res.status === 404 || !res.ok) {
        if (tripDashboardLoading) tripDashboardLoading.remove();
        tripDashboardContent.innerHTML = "<p>Trip not found.</p>";
        return;
      }
      const data = await res.json();
      if (tripDashboardLoading) tripDashboardLoading.remove();
      renderTripDashboard(data);
    } catch (_) {
      if (tripDashboardLoading) tripDashboardLoading.remove();
      tripDashboardContent.innerHTML = "<p>Could not load trip.</p>";
    }
  }

  if (tripDashboardContent && tripIdParam) {
    loadTripDashboard();
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

      const typeSelect = document.querySelector("#gear-type");
      const typeOption = typeSelect && typeSelect.options[typeSelect.selectedIndex];
      const requirement_type_id = typeOption && typeOption.value ? parseInt(typeOption.value, 10) : undefined;
      const typeDisplay = typeOption && typeOption.textContent ? typeOption.textContent.trim() : "Other";

      const payload = {
        type: typeDisplay,
        name,
        capacity: document.querySelector("#gear-capacity").value.trim() || undefined,
        brand: document.querySelector("#gear-brand").value.trim() || undefined,
        condition: document.querySelector("#gear-condition").value.trim() || undefined,
        notes: document.querySelector("#gear-notes").value.trim() || undefined,
      };
      if (requirement_type_id && !Number.isNaN(requirement_type_id)) {
        payload.requirement_type_id = requirement_type_id;
      }
      const capPersonsEl = document.querySelector("#gear-capacity-persons");
      if (capPersonsEl && capPersonsEl.value !== "" && capPersonsEl.value != null) {
        const cp = parseInt(capPersonsEl.value, 10);
        if (!Number.isNaN(cp) && cp >= 1) payload.capacity_persons = cp;
      }

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
          if (typeSelect) typeSelect.selectedIndex = 0;
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

// Inventory Nav (when already on page)
const home = document.querySelector("#home");
if (home) {
  home.addEventListener("click", () => {
    window.location.href = "dashboard.html";
  });
}

// Back button (Trip Dashboard)
const backToTrips = document.querySelector("#back-to-trips");
if (backToTrips) {
  backToTrips.addEventListener("click", () => {
    window.location.href = "trip.html";
  });
}