/**
 * Trip dashboard page (trip_dashboard.html?id=...): summary, weather, map, team, gear pool, checklist.
 */
import { API_BASE } from "./config.js";
import { escapeHtml, getWeatherIcon } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const tripDashboardContent = document.querySelector("#trip-dashboard-content");
  const tripDashboardLoading = document.querySelector("#trip-dashboard-loading");
  const tripViewToggleButtons = Array.from(document.querySelectorAll(".trip-view-toggle-btn"));
  const tripDashboardToggleWrap = document.querySelector(".trip-dashboard-view-toggle");
  const tripDashboardSummarySection = document.querySelector(".trip-dashboard-summary");
  const tripDashboardNotesPanel = document.querySelector("#trip-dashboard-notes-panel");
  const tripDashboardGearBlock = document.querySelector(".trip-dashboard-block.trip-dashboard-gear");
  const tripDashboardTeamBlock = document.querySelector(".trip-dashboard-block.trip-dashboard-team");
  const tripDashboardInvitedSection = document.querySelector("#trip-dashboard-invited");
  const params = new URLSearchParams(window.location.search);
  const tripIdParam = params.get("id");
  let tripWeatherResult = null;

  if (!tripDashboardContent) return;

  function showBlock(el) {
    if (!el) return;
    el.style.display = "";
  }

  function hideBlock(el) {
    if (!el) return;
    el.style.display = "none";
  }

  function setTripDashboardView(view) {
    const next = view === "pack" ? "pack" : "trip";
    if (tripViewToggleButtons.length) {
      tripViewToggleButtons.forEach((btn) => {
        const isActive = btn.getAttribute("data-view") === next;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-pressed", isActive ? "true" : "false");
      });
    }
    if (next === "pack") {
      hideBlock(tripDashboardSummarySection);
      hideBlock(tripDashboardNotesPanel);
      hideBlock(tripDashboardTeamBlock);
      hideBlock(tripDashboardInvitedSection);
      showBlock(tripDashboardGearBlock);
    } else {
      showBlock(tripDashboardSummarySection);
      showBlock(tripDashboardNotesPanel);
      showBlock(tripDashboardTeamBlock);
      showBlock(tripDashboardInvitedSection);
      hideBlock(tripDashboardGearBlock);
    }
  }

  if (tripDashboardToggleWrap && tripViewToggleButtons.length) {
    tripViewToggleButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const v = btn.getAttribute("data-view") || "trip";
        setTripDashboardView(v);
      });
    });
    setTripDashboardView("trip");
  }

  function applyTripWeather(body) {
    const loadingEl = document.getElementById("trip-weather-loading");
    const bodyEl = document.getElementById("trip-weather-body");
    if (!loadingEl && !bodyEl) return;
    if (loadingEl) loadingEl.remove();
    if (!bodyEl) return;
    if (!body) {
      bodyEl.innerHTML = "<p>Forecast unavailable. Try again later.</p>";
      return;
    }
    if (body.error === "no_coordinates") {
      bodyEl.innerHTML = "<p>No coordinates available for weather.</p>";
      return;
    }
    if (body.error === "forecast_unavailable") {
      bodyEl.innerHTML = "<p>Forecast unavailable. Try again later.</p>";
      return;
    }
    const label = body.is_trip_date
      ? "Weather for " + (body.for_date || "").slice(0, 10)
      : "Current weather";
    const iconName = getWeatherIcon(body.shortForecast);
    const iconAlt = iconName.replace(/_/g, " ");
    let html = "<div class=\"trip-weather-header\"><img class=\"trip-weather-icon\" src=\"images_for_site/weather_icons/" + iconName + ".png\" alt=\"" + escapeHtml(iconAlt) + "\" /><p><strong>" + escapeHtml(label) + "</strong>";
    if (body.temperature != null) {
      html += " — " + escapeHtml(String(body.temperature)) + "°" + (body.temperatureUnit || "F");
    }
    html += "</p></div>";
    if (body.shortForecast) {
      html += "<p>" + escapeHtml(body.shortForecast) + "</p>";
    }
    if (body.detailedForecast) {
      html += "<p class=\"trip-weather-detailed\">" + escapeHtml(body.detailedForecast).replace(/\n/g, "<br>") + "</p>";
    }
    bodyEl.innerHTML = html;
  }

  function renderTripDashboard(data) {
    const trip = data.trip;
    const pendingInvite = data.pending_invite || null;
    const locationSummary = data.location_summary || null;
    const bannerH1 = document.querySelector(".banner h1");
    if (bannerH1) bannerH1.textContent = trip.trip_name || "Trip";
    let tripInfoHtml =
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
      if (stats.length) tripInfoHtml += `<p class="trip-dashboard-trail-stats"><strong>Trail info:</strong> ${stats.join(" · ")}</p>`;
    }
    if (trip.is_creator) {
      tripInfoHtml += `<p class="trip-dashboard-actions"><button type="button" id="edit-trip-btn-dashboard" class="secondary">Edit trip</button> <button type="button" id="delete-trip-btn-dashboard" class="secondary">Delete trip</button></p>`;
    } else {
      tripInfoHtml += `<p class="trip-dashboard-actions"><button type="button" id="leave-trip-btn-dashboard" class="secondary">Leave trip</button></p>`;
    }

    const mapLat = (locationSummary && locationSummary.lat != null) ? String(locationSummary.lat).trim() : "";
    const mapLng = (locationSummary && locationSummary.long != null) ? String(locationSummary.long).trim() : "";
    const hasCoords = Boolean(mapLat && mapLng);
    const mapQuery = hasCoords ? encodeURIComponent(`${mapLat},${mapLng}`) : "";

    let weatherBlockHtml = `<section class="trip-dashboard-weather" aria-label="Weather"><h3>Weather</h3>`;
    weatherBlockHtml += `<p id="trip-weather-loading">Loading weather…</p><div id="trip-weather-body" class="trip-weather-body"></div>`;
    weatherBlockHtml += `</section>`;

    let summaryHtml =
      `<div class="trip-dashboard-top">
         <div class="trip-dashboard-trip-info">${tripInfoHtml}</div>
         <div class="trip-dashboard-weather-top">${weatherBlockHtml}</div>
       </div>`;

    summaryHtml += `<section class="trip-dashboard-map" aria-label="Trail map">
        <h3>Map</h3>
        ${hasCoords ? `
          <iframe
            class="trip-dashboard-map-frame"
            title="Google map"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            src="https://www.google.com/maps?q=${mapQuery}&z=12&output=embed"
          ></iframe>
          <p class="trip-dashboard-map-links">
            <a href="https://www.google.com/maps/search/?api=1&query=${mapQuery}" target="_blank" rel="noopener">Open in Google Maps</a>
          </p>
        ` : `
          <p class="trip-dashboard-map-placeholder">No coordinates available for this trip location.</p>
        `}
      </section>`;

    if (locationSummary) {
      const summaryText = (locationSummary.summarized_description || "").trim();
      const r1 = (locationSummary.trip_report_1 || "").trim();
      const r2 = (locationSummary.trip_report_2 || "").trim();
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
    if (tripWeatherResult) applyTripWeather(tripWeatherResult);

    const notesTextarea = document.getElementById("trip-notes-textarea");
    const notesSaveBtn = document.getElementById("trip-notes-save");
    if (tripDashboardNotesPanel) tripDashboardNotesPanel.style.display = "block";
    if (notesTextarea) notesTextarea.value = trip.notes || "";
    if (notesSaveBtn && tripIdParam) {
      notesSaveBtn.onclick = async () => {
        const notesVal = notesTextarea ? notesTextarea.value : "";
        const payload = {
          trip_name: trip.trip_name || "",
          trip_report_info_id: trip.trip_report_info_id,
          activity_type: trip.activity_type || "",
          intended_start_date: trip.intended_start_date ? String(trip.intended_start_date).slice(0, 10) : undefined,
          notes: notesVal,
        };
        try {
          const res = await fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripIdParam), {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (res.ok) {
            trip.notes = notesVal;
            notesSaveBtn.textContent = "Saved";
            setTimeout(() => { notesSaveBtn.textContent = "Save notes"; }, 2000);
          } else {
            const data = await res.json().catch(() => ({}));
            alert(data.error || "Could not save notes");
          }
        } catch (_) {
          alert("Could not save notes. Try again.");
        }
      };
    }

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
    if (editBtnDash && tripIdParam && window.openEditTripModal) {
      editBtnDash.addEventListener("click", () => window.openEditTripModal(tripIdParam));
    }
    if (deleteBtnDash && tripIdParam && window.tripsDeleteTrip) {
      deleteBtnDash.addEventListener("click", () => {
        if (confirm("Delete this trip? This cannot be undone.")) {
          window.tripsDeleteTrip(tripIdParam).then(() => { window.location.href = "trip.html"; }).catch((err) => alert(err.message || "Could not delete trip"));
        }
      });
    }
    const leaveTripBtnDash = document.querySelector("#leave-trip-btn-dashboard");
    if (leaveTripBtnDash && tripIdParam && window.tripsLeaveTrip) {
      leaveTripBtnDash.addEventListener("click", () => {
        if (confirm("Leave this trip? You can be re-invited later.")) {
          window.tripsLeaveTrip(tripIdParam).then(() => { window.location.href = "trip.html"; }).catch((err) => alert(err.message || "Could not leave trip"));
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
          ? collaborators.map((c) => {
              const kickBtn = trip.is_creator && c.role !== "creator"
                ? ` <button type="button" class="secondary kick-member-btn" data-user-id="${c.id}">Kick</button>`
                : "";
              return `<p>${escapeHtml(c.username)} <span class="role-badge">${escapeHtml(c.role)}</span>${kickBtn}</p>`;
            }).join("")
          : "<p>No members yet.</p>";
        if (tripIdParam && trip.is_creator && window.tripsKickTripMember) {
          listEl.querySelectorAll(".kick-member-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
              const userId = btn.getAttribute("data-user-id");
              if (!userId || !confirm("Remove this member from the trip?")) return;
              try {
                await window.tripsKickTripMember(tripIdParam, userId);
                loadTripDashboard();
              } catch (err) {
                alert(err.message || "Could not remove member");
              }
            });
          });
        }
      }
    }

    if (trip.is_creator) {
      const pendingInvitesList = data.pending_invites || [];
      if (pendingSection && pendingInvitesList.length > 0) {
        pendingSection.style.display = "block";
        const listEl = document.querySelector("#trip-pending-invites-list");
        if (listEl) {
          listEl.innerHTML = pendingInvitesList.map((p) =>
            `<p>${escapeHtml(p.invitee_username)} (pending) <button type="button" class="secondary cancel-invite-btn" data-invite-id="${p.id}">Cancel invite</button></p>`
          ).join("");
          if (tripIdParam && window.tripsCancelTripInvite) {
            listEl.querySelectorAll(".cancel-invite-btn").forEach((btn) => {
              btn.addEventListener("click", async () => {
                const inviteId = btn.getAttribute("data-invite-id");
                if (!inviteId || !confirm("Cancel this invite?")) return;
                try {
                  await window.tripsCancelTripInvite(inviteId);
                  loadTripDashboard();
                } catch (err) {
                  alert(err.message || "Could not cancel invite");
                }
              });
            });
          }
        }
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
      const weatherPromise = fetch(API_BASE + "/api/trips/" + encodeURIComponent(tripIdParam) + "/weather", { credentials: "include" })
        .then((r) => r.json())
        .catch(() => ({ error: "forecast_unavailable" }));
      weatherPromise.then((body) => {
        tripWeatherResult = body;
        applyTripWeather(body);
      });
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

  window.loadTripDashboard = loadTripDashboard;

  if (tripIdParam) {
    loadTripDashboard();
  } else {
    tripDashboardLoading.remove();
    tripDashboardContent.innerHTML = "<p>No trip selected. <a href=\"trip.html\">Back to trips</a></p>";
  }
});
