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

  // ---------- Banner: show "Welcome, {username}" only on dashboard (not inventory/trip/friends) ----------
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

  // ---------- Inventory (Gear Library dashboard): load gear by category and add form ----------
  const gearCategoriesEl = document.querySelector("#gear-categories");
  const gearLoadingEl = document.querySelector("#gear-loading");
  const addItemForm = document.querySelector("#add-item-form");
  let gearEditMode = false;
  let lastGearItems = [];

  function getCategoryForKey(key) {
    if (!key) return "Other";
    return REQUIREMENT_KEY_TO_CATEGORY[key] || "Other";
  }

  function renderGearList(items) {
    if (!gearCategoriesEl || items.length === 0) return;
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
            const liClass = gearEditMode ? "gear-category-item gear-item-editable" : "gear-category-item";
            const dataId = gearEditMode ? ` data-gear-id="${item.id}"` : "";
            return `<li class="${liClass}"${dataId}><strong>${escapeHtml(typeLabel)}</strong>: ${escapeHtml(item.name || "—")}${item.condition || item.notes ? ` <span class="gear-meta">${[item.condition, item.notes].filter(Boolean).map(escapeHtml).join(" — ")}</span>` : ""}${meta ? ` <span class="gear-meta">${meta}</span>` : ""}</li>`;
          })
          .join("");
        return `<div class="gear-category-section"><h3>${escapeHtml(category)}</h3><ul>${listItems}</ul></div>`;
      })
      .join("");
    gearCategoriesEl.innerHTML = html;
    if (gearEditMode) {
      gearCategoriesEl.querySelectorAll(".gear-item-editable").forEach((el) => {
        el.addEventListener("click", () => {
          const id = el.getAttribute("data-gear-id");
          if (id) openEditGearPanel(id);
        });
      });
    }
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
      lastGearItems = items;
      if (gearLoadingEl) gearLoadingEl.remove();
      if (items.length === 0) {
        gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">No gear yet. Add some in the form on the right.</p>";
        return;
      }
      renderGearList(items);
    } catch (_) {
      if (gearLoadingEl) gearLoadingEl.remove();
      gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">Could not load gear.</p>";
    }
  }

  const editGearSection = document.querySelector("#edit-gear-section");
  const editGearForm = document.querySelector("#edit-gear-form");
  const editGearIdEl = document.querySelector("#edit-gear-id");
  const editGearNameEl = document.querySelector("#edit-gear-name");
  const editGearTypeSelect = document.querySelector("#edit-gear-type");
  const editGearCapacityEl = document.querySelector("#edit-gear-capacity");
  const editGearCapacityPersonsEl = document.querySelector("#edit-gear-capacity-persons");
  const editGearWeightEl = document.querySelector("#edit-gear-weight");
  const editGearBrandEl = document.querySelector("#edit-gear-brand");
  const editGearConditionEl = document.querySelector("#edit-gear-condition");
  const editGearNotesEl = document.querySelector("#edit-gear-notes");
  const editGearErrorEl = document.querySelector("#edit-gear-error");
  const editGearCancelBtn = document.querySelector("#edit-gear-cancel");
  const editGearDeleteBtn = document.querySelector("#edit-gear-delete-btn");

  async function loadEditGearTypes() {
    if (!editGearTypeSelect) return;
    try {
      const res = await fetch(API_BASE + "/api/requirement-types", { credentials: "include" });
      if (!res.ok) return;
      const types = await res.json();
      editGearTypeSelect.innerHTML = (types.length === 0 ? [] : types)
        .map((t) => `<option value="${t.id}">${escapeHtml(t.display_name)}</option>`)
        .join("") || "<option value=\"\">Other</option>";
    } catch (_) {}
  }

  function closeEditGearPanel() {
    if (editGearSection) editGearSection.style.display = "none";
    if (editGearErrorEl) editGearErrorEl.textContent = "";
  }

  async function openEditGearPanel(gearId) {
    if (!editGearSection || !editGearForm) return;
    if (editGearErrorEl) editGearErrorEl.textContent = "";
    try {
      const res = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(gearId), { credentials: "include" });
      if (!res.ok) return;
      const item = await res.json();
      await loadEditGearTypes();
      if (editGearIdEl) editGearIdEl.value = item.id;
      if (editGearNameEl) editGearNameEl.value = item.name || "";
      if (editGearCapacityEl) editGearCapacityEl.value = item.capacity || "";
      if (editGearCapacityPersonsEl) editGearCapacityPersonsEl.value = item.capacity_persons != null ? item.capacity_persons : "";
      if (editGearWeightEl) editGearWeightEl.value = item.weight_oz != null ? item.weight_oz : "";
      if (editGearBrandEl) editGearBrandEl.value = item.brand || "";
      if (editGearConditionEl) editGearConditionEl.value = item.condition || "";
      if (editGearNotesEl) editGearNotesEl.value = item.notes || "";
      if (editGearTypeSelect) {
        const rtId = item.requirement_type_id;
        const opt = Array.from(editGearTypeSelect.options).find((o) => o.value === String(rtId));
        if (opt) editGearTypeSelect.value = String(rtId);
        else if (editGearTypeSelect.options.length) editGearTypeSelect.selectedIndex = 0;
      }
      editGearSection.style.display = "block";
    } catch (_) {}
  }

  if (editGearForm) {
    editGearForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = editGearIdEl && editGearIdEl.value;
      if (!id || !editGearNameEl) return;
      if (editGearErrorEl) editGearErrorEl.textContent = "";
      const typeOption = editGearTypeSelect && editGearTypeSelect.options[editGearTypeSelect.selectedIndex];
      const requirement_type_id = typeOption && typeOption.value ? parseInt(typeOption.value, 10) : undefined;
      const typeDisplay = typeOption && typeOption.textContent ? typeOption.textContent.trim() : "Other";
      const payload = {
        type: typeDisplay,
        name: editGearNameEl.value.trim(),
        capacity: editGearCapacityEl ? editGearCapacityEl.value.trim() || undefined : undefined,
        brand: editGearBrandEl ? editGearBrandEl.value.trim() || undefined : undefined,
        condition: editGearConditionEl ? editGearConditionEl.value.trim() || undefined : undefined,
        notes: editGearNotesEl ? editGearNotesEl.value.trim() || undefined : undefined,
      };
      if (requirement_type_id && !Number.isNaN(requirement_type_id)) payload.requirement_type_id = requirement_type_id;
      if (editGearCapacityPersonsEl && editGearCapacityPersonsEl.value !== "" && editGearCapacityPersonsEl.value != null) {
        const cp = parseInt(editGearCapacityPersonsEl.value, 10);
        if (!Number.isNaN(cp) && cp >= 1) payload.capacity_persons = cp;
      }
      if (editGearWeightEl && editGearWeightEl.value !== "" && editGearWeightEl.value != null) {
        const w = parseFloat(editGearWeightEl.value);
        if (!Number.isNaN(w) && w >= 0) payload.weight_oz = w;
      }
      try {
        const r = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(id), {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (r.ok) {
          closeEditGearPanel();
          loadGear();
          return;
        }
        const data = await r.json().catch(() => ({}));
        if (editGearErrorEl) editGearErrorEl.textContent = data.error || "Could not update item.";
      } catch (_) {
        if (editGearErrorEl) editGearErrorEl.textContent = "Could not reach the server.";
      }
    });
  }
  if (editGearCancelBtn) editGearCancelBtn.addEventListener("click", closeEditGearPanel);
  if (editGearDeleteBtn) {
    editGearDeleteBtn.addEventListener("click", async () => {
      const id = editGearIdEl && editGearIdEl.value;
      if (!id) return;
      try {
        const r = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(id), { method: "DELETE", credentials: "include" });
        if (r.ok) {
          closeEditGearPanel();
          loadGear();
          return;
        }
      } catch (_) {}
    });
  }

  const editGearBtn = document.querySelector("#edit-gear-btn");
  if (editGearBtn) {
    editGearBtn.addEventListener("click", () => {
      gearEditMode = !gearEditMode;
      editGearBtn.textContent = gearEditMode ? "Done" : "Edit gear";
      if (!gearEditMode) closeEditGearPanel();
      if (lastGearItems.length) renderGearList(lastGearItems);
    });
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

  // ---------- Friends page: My favorite hikes ----------
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

  // ---------- Trip list and create trip ----------
  const tripList = document.querySelector("#trip-list");
  const createTripForm = document.querySelector("#create-trip-form");

  let currentUserId = null;
  let tripEditMode = false;
  let lastTrips = [];

  function renderTripList(trips) {
    if (!tripList || !trips.length) return;
    const isCreator = (t) => currentUserId != null && t.creator_id === currentUserId;
    const showActions = tripEditMode;
    tripList.innerHTML = trips
      .map(
        (t) => {
          let actions = "";
          if (showActions) {
            if (isCreator(t)) {
              actions = `<div class="trip-actions"><button type="button" class="trip-edit-btn secondary" data-trip-id="${t.id}">Edit</button><button type="button" class="trip-delete-btn secondary" data-trip-id="${t.id}">Delete</button></div>`;
            } else {
              actions = `<div class="trip-actions"><button type="button" class="trip-disband-btn secondary" data-trip-id="${t.id}">Disband</button></div>`;
            }
          }
          return `<div class="trip-card trip-card-clickable" data-trip-id="${t.id}">
              <div class="trip-card-body">
                <h3>${escapeHtml(t.trip_name || "Unnamed")}</h3>
                <p><strong>Trail:</strong> ${escapeHtml(t.trail_name || "—")}</p>
                <p><strong>Activity:</strong> ${escapeHtml(t.activity_type || "—")}</p>
                <p><strong>Start:</strong> ${t.intended_start_date ? escapeHtml(String(t.intended_start_date).slice(0, 10)) : "—"}</p>
                <p><strong>Created by:</strong> ${escapeHtml(t.creator_username || "—")}</p>
              </div>
              ${actions}
            </div>`;
        }
      )
      .join("");
    tripList.querySelectorAll(".trip-card-clickable").forEach((el) => {
      el.addEventListener("click", (e) => {
        if (e.target.closest(".trip-actions")) return;
        const id = el.getAttribute("data-trip-id");
        window.location.href = "trip_dashboard.html?id=" + encodeURIComponent(id);
      });
    });
    tripList.querySelectorAll(".trip-edit-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        openEditTripModal(btn.getAttribute("data-trip-id"));
      });
    });
    tripList.querySelectorAll(".trip-delete-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.getAttribute("data-trip-id");
        if (confirm("Delete this trip? This cannot be undone.")) {
          deleteTrip(id).then(() => loadTrips()).catch((err) => alert(err.message || "Could not delete trip"));
        }
      });
    });
    tripList.querySelectorAll(".trip-disband-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.getAttribute("data-trip-id");
        if (confirm("Leave this trip? You can be re-invited later.")) {
          leaveTrip(id).then(() => loadTrips()).catch((err) => alert(err.message || "Could not leave trip"));
        }
      });
    });
  }

  async function loadTrips() {
    if (!tripList) return;
    try {
      const meRes = await fetch(API_BASE + "/api/me", { credentials: "include" });
      if (meRes.ok) {
        const me = await meRes.json();
        currentUserId = me.id != null ? me.id : null;
      }
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
      lastTrips = trips;
      if (trips.length === 0) {
        tripList.innerHTML = "<p>No trips yet. Create one below.</p>";
        return;
      }
      renderTripList(trips);
    } catch (_) {
      tripList.innerHTML = "<p>Could not load trips.</p>";
    }
  }

  const editTripsBtn = document.querySelector("#edit-trips-btn");
  if (editTripsBtn) {
    editTripsBtn.addEventListener("click", () => {
      tripEditMode = !tripEditMode;
      editTripsBtn.textContent = tripEditMode ? "Done" : "Edit trips";
      if (!tripEditMode) closeEditTripModal();
      if (lastTrips.length) renderTripList(lastTrips);
    });
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

  // ---------- Edit trip modal and delete ----------
  const editTripModal = document.querySelector("#edit-trip-modal");
  const editTripForm = document.querySelector("#edit-trip-form");
  const editTripIdEl = document.querySelector("#edit-trip-id");
  const editTripNameEl = document.querySelector("#edit-trip-name");
  const editTripLocationSearch = document.querySelector("#edit-trip-location-search");
  const editTripReportInfoIdEl = document.querySelector("#edit-trip-report-info-id");
  const editTripLocationListbox = document.querySelector("#edit-trip-location-listbox");
  const editTripActivityEl = document.querySelector("#edit-trip-activity");
  const editTripDateEl = document.querySelector("#edit-trip-date");
  const editTripErrorEl = document.querySelector("#edit-trip-error");
  const editTripCancelBtn = document.querySelector("#edit-trip-cancel");
  const editTripCombobox = document.querySelector(".edit-trip-combobox");

  function closeEditTripModal() {
    if (editTripModal) editTripModal.style.display = "none";
    if (editTripErrorEl) editTripErrorEl.textContent = "";
  }

  async function deleteTrip(tripId) {
    const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripId), {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Could not delete trip");
    }
  }

  async function leaveTrip(tripId) {
    const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripId) + "/leave", {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Could not leave trip");
    }
  }

  function renderEditLocationOptions(locations) {
    if (!editTripLocationListbox) return;
    if (!locations || locations.length === 0) {
      editTripLocationListbox.innerHTML = '<li role="option" class="location-no-results">No matching trails. Type to search the catalog.</li>';
      return;
    }
    editTripLocationListbox.innerHTML = locations.map((loc) => {
      const meta = [loc.distance, loc.elevation_gain, loc.difficulty].filter(Boolean).join(" · ");
      return `<li role="option" data-id="${loc.id}" data-hike-name="${escapeHtml(loc.hike_name || "")}">${escapeHtml(loc.hike_name || "Unnamed")}${meta ? `<div class="location-option-meta">${escapeHtml(meta)}</div>` : ""}</li>`;
    }).join("");
  }

  async function openEditTripModal(tripId) {
    if (!editTripModal || !editTripForm) return;
    if (editTripErrorEl) editTripErrorEl.textContent = "";
    try {
      const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripId), { credentials: "include" });
      if (!res.ok) return;
      const trip = await res.json();
      if (editTripIdEl) editTripIdEl.value = tripId;
      if (editTripNameEl) editTripNameEl.value = trip.trip_name || "";
      if (editTripActivityEl) editTripActivityEl.value = trip.activity_type || "";
      if (editTripDateEl) editTripDateEl.value = trip.intended_start_date ? String(trip.intended_start_date).slice(0, 10) : "";
      const infoId = trip.trip_report_info_id;
      if (editTripReportInfoIdEl) editTripReportInfoIdEl.value = infoId != null ? infoId : "";
      if (editTripLocationSearch) editTripLocationSearch.value = trip.trail_name || "";
      if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "false");
      editTripModal.style.display = "flex";
    } catch (_) {}
  }

  if (editTripForm) {
    editTripForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (editTripErrorEl) editTripErrorEl.textContent = "";
      const id = editTripIdEl && editTripIdEl.value;
      if (!id) return;
      const trip_report_info_id = editTripReportInfoIdEl && editTripReportInfoIdEl.value.trim();
      if (!trip_report_info_id) {
        if (editTripErrorEl) editTripErrorEl.textContent = "Please select a location from the catalog.";
        return;
      }
      const payload = {
        trip_name: (editTripNameEl && editTripNameEl.value.trim()) || "",
        trip_report_info_id: parseInt(trip_report_info_id, 10),
        activity_type: editTripActivityEl && editTripActivityEl.value,
        intended_start_date: (editTripDateEl && editTripDateEl.value) || undefined,
      };
      try {
        const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(id), {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          closeEditTripModal();
          if (tripList) loadTrips();
          if (typeof loadTripDashboard === "function") loadTripDashboard();
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (editTripErrorEl) editTripErrorEl.textContent = data.error || "Could not update trip.";
      } catch (_) {
        if (editTripErrorEl) editTripErrorEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }
  if (editTripCancelBtn) editTripCancelBtn.addEventListener("click", closeEditTripModal);
  if (editTripModal) {
    const backdrop = editTripModal.querySelector(".edit-trip-modal-backdrop");
    if (backdrop) backdrop.addEventListener("click", closeEditTripModal);
  }
  if (editTripLocationSearch && editTripLocationListbox) {
    editTripLocationSearch.addEventListener("focus", () => {
      if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "true");
      renderEditLocationOptions(filterLocations(editTripLocationSearch.value));
    });
    editTripLocationSearch.addEventListener("input", () => {
      editTripReportInfoIdEl.value = "";
      if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "true");
      renderEditLocationOptions(filterLocations(editTripLocationSearch.value));
    });
    editTripLocationSearch.addEventListener("blur", () => {
      setTimeout(() => { if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "false"); }, 200);
    });
    editTripLocationListbox.addEventListener("click", (e) => {
      const opt = e.target.closest("[role=option][data-id]");
      if (opt) {
        e.preventDefault();
        editTripReportInfoIdEl.value = opt.getAttribute("data-id");
        editTripLocationSearch.value = opt.getAttribute("data-hike-name") || "";
        if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "false");
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
    if (locationSummary) {
      const stats = [];
      if (locationSummary.distance) stats.push(`Distance: ${escapeHtml(locationSummary.distance)}`);
      if (locationSummary.elevation_gain) stats.push(`Elevation gain: ${escapeHtml(locationSummary.elevation_gain)}`);
      if (locationSummary.highpoint) stats.push(`Highpoint: ${escapeHtml(locationSummary.highpoint)}`);
      if (locationSummary.difficulty) stats.push(`Difficulty: ${escapeHtml(locationSummary.difficulty)}`);
      if (locationSummary.lat != null && locationSummary.long != null && String(locationSummary.lat).trim() && String(locationSummary.long).trim()) {
        stats.push(`Coordinates: ${escapeHtml(String(locationSummary.lat).trim())}, ${escapeHtml(String(locationSummary.long).trim())}`);
      }
      if (stats.length) summaryHtml += `<p class="trip-dashboard-trail-stats"><strong>Trail info:</strong> ${stats.join(" · ")}</p>`;
    }
    if (trip.is_creator) {
      summaryHtml += `<p class="trip-dashboard-actions"><button type="button" id="edit-trip-btn-dashboard" class="secondary">Edit trip</button> <button type="button" id="delete-trip-btn-dashboard" class="secondary">Delete trip</button></p>`;
    } else {
      summaryHtml += `<p class="trip-dashboard-actions"><button type="button" id="leave-trip-btn-dashboard" class="secondary">Leave trip</button></p>`;
    }
    if (locationSummary) {
      const summaryText = (locationSummary.summarized_description || "").trim();
      const r1 = (locationSummary.trip_report_1 || "").trim();
      const r2 = (locationSummary.trip_report_2 || "").trim();
      const defaultVal = "summary";
      summaryHtml += `<section class="trip-dashboard-location-summary" aria-label="Trail report summary">
         <h3>Trail report summary</h3>
         <div class="trip-dashboard-report-controls">
           <label for="trip-dashboard-report-select">Show:</label>
           <select id="trip-dashboard-report-select" class="trip-dashboard-report-select" aria-label="Select report or summary">
             <option value="summary">AI summary</option>
             <option value="report1">Trip report 1</option>
             <option value="report2">Trip report 2</option>
           </select>
         </div>
         <div id="trip-dashboard-report-body" class="trip-dashboard-ai-summary">${summaryText ? escapeHtml(summaryText).replace(/\n/g, "<br>") : "No report available."}</div>
         ${locationSummary.source_url ? `<p><a href="${escapeHtml(locationSummary.source_url)}" target="_blank" rel="noopener">View source</a></p>` : ""}
       </section>`;
    }
    tripDashboardContent.innerHTML = summaryHtml;

    if (locationSummary) {
      const reportBody = document.getElementById("trip-dashboard-report-body");
      const reportSelect = document.getElementById("trip-dashboard-report-select");
      const summaryText = (locationSummary.summarized_description || "").trim();
      const r1 = (locationSummary.trip_report_1 || "").trim();
      const r2 = (locationSummary.trip_report_2 || "").trim();
      function setBody(value) {
        if (!reportBody) return;
        let html;
        if (value === "summary") html = summaryText ? escapeHtml(summaryText).replace(/\n/g, "<br>") : "No report available.";
        else if (value === "report1") html = r1 ? escapeHtml(r1).replace(/\n/g, "<br>") : "No report available.";
        else if (value === "report2") html = r2 ? escapeHtml(r2).replace(/\n/g, "<br>") : "No report available.";
        else html = "No report available.";
        reportBody.innerHTML = html;
      }
      if (reportSelect) {
        reportSelect.addEventListener("change", () => setBody(reportSelect.value));
      }
    }

    const editBtnDash = document.querySelector("#edit-trip-btn-dashboard");
    const deleteBtnDash = document.querySelector("#delete-trip-btn-dashboard");
    if (editBtnDash && tripIdParam) {
      editBtnDash.addEventListener("click", () => openEditTripModal(tripIdParam));
    }
    if (deleteBtnDash && tripIdParam) {
      deleteBtnDash.addEventListener("click", () => {
        if (confirm("Delete this trip? This cannot be undone.")) {
          deleteTrip(tripIdParam).then(() => { window.location.href = "trip.html"; }).catch((err) => alert(err.message || "Could not delete trip"));
        }
      });
    }
    const leaveTripBtnDash = document.querySelector("#leave-trip-btn-dashboard");
    if (leaveTripBtnDash && tripIdParam) {
      leaveTripBtnDash.addEventListener("click", () => {
        if (confirm("Leave this trip? You can be re-invited later.")) {
          leaveTrip(tripIdParam).then(() => { window.location.href = "trip.html"; }).catch((err) => alert(err.message || "Could not leave trip"));
        }
      });
    }

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