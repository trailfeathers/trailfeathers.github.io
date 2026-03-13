/**
 * Trip planner page: trip list, create trip, edit modal, trip invites, location catalog.
 */
import { API_BASE } from "./config.js";
import { escapeHtml } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
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

  // Location catalog: searchable combobox
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
        notes: (document.querySelector("#trip-notes") && document.querySelector("#trip-notes").value) || "",
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

  // Edit trip modal and delete/leave/kick/cancel
  const editTripModal = document.querySelector("#edit-trip-modal");
  const editTripForm = document.querySelector("#edit-trip-form");
  const editTripIdEl = document.querySelector("#edit-trip-id");
  const editTripNameEl = document.querySelector("#edit-trip-name");
  const editTripLocationSearch = document.querySelector("#edit-trip-location-search");
  const editTripReportInfoIdEl = document.querySelector("#edit-trip-report-info-id");
  const editTripLocationListbox = document.querySelector("#edit-trip-location-listbox");
  const editTripActivityEl = document.querySelector("#edit-trip-activity");
  const editTripDateEl = document.querySelector("#edit-trip-date");
  const editTripNotesEl = document.querySelector("#edit-trip-notes");
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

  async function kickTripMember(tripId, userId) {
    const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripId) + "/collaborators/" + encodeURIComponent(userId), {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Could not remove member");
    }
  }

  async function cancelTripInvite(inviteId) {
    const res = await fetch(API_BASE + "/api/trip-invites/" + encodeURIComponent(inviteId), {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Could not cancel invite");
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
      if (editTripNotesEl) editTripNotesEl.value = trip.notes || "";
      const infoId = trip.trip_report_info_id;
      if (editTripReportInfoIdEl) editTripReportInfoIdEl.value = infoId != null ? infoId : "";
      if (editTripLocationSearch) editTripLocationSearch.value = trip.trail_name || "";
      if (editTripCombobox) editTripCombobox.setAttribute("aria-expanded", "false");
      editTripModal.style.display = "flex";
    } catch (_) {}
  }

  // Expose for trip-dashboard (Edit trip button)
  window.openEditTripModal = openEditTripModal;
  window.tripsDeleteTrip = deleteTrip;
  window.tripsLeaveTrip = leaveTrip;
  window.tripsKickTripMember = kickTripMember;
  window.tripsCancelTripInvite = cancelTripInvite;

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
        notes: (editTripNotesEl && editTripNotesEl.value) || "",
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
          if (typeof window.loadTripDashboard === "function") window.loadTripDashboard();
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
});
