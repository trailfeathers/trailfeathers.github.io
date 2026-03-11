const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

function escapeHtml(text) {
  if (text == null) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function getLocationsOptionsHtml(locations, excludeIds = []) {
  const set = new Set(excludeIds);
  let html = '<option value="">Choose a hike…</option>';
  (locations || []).forEach(function (loc) {
    if (set.has(loc.id)) return;
    html += '<option value="' + loc.id + '">' + escapeHtml(loc.hike_name || "") + '</option>';
  });
  return html;
}

(function () {
  let locations = [];
  /** Hikes user can put in top four (must have trip report). Same shape as locations: id, hike_name */
  let topFourEligible = [];

  function apiFetch(path, options) {
    return fetch(API_BASE + path, Object.assign({ credentials: "include" }, options || {}));
  }

  function redirectToLogin() {
    window.location.href = "../login.html";
  }

  function initNav() {
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        apiFetch("/api/logout", { method: "POST" }).then(function () {
          window.location.href = "../login.html";
        });
      });
    }
    const home = document.getElementById("home");
    const inventory = document.getElementById("inventory");
    const planTrip = document.getElementById("plan-trip");
    if (home) home.addEventListener("click", function () { window.location.href = "../dashboard.html"; });
    if (inventory) inventory.addEventListener("click", function () { window.location.href = "../inventory.html"; });
    if (planTrip) planTrip.addEventListener("click", function () { window.location.href = "../trip.html"; });
  }

  function staticBaseForSocialPage() {
    // friends.html lives in static/social center/ — static assets are ../ from here
    return "../";
  }

  function setProfilePictureCircle(data) {
    const img = document.getElementById("profile-picture-img");
    const placeholder = document.getElementById("profile-picture-placeholder");
    if (!img || !placeholder) return;
    if (data && data.avatar_path) {
      img.src = staticBaseForSocialPage() + data.avatar_path;
      img.classList.remove("hidden");
      placeholder.classList.add("hidden");
      return;
    }
    img.removeAttribute("src");
    img.classList.add("hidden");
    placeholder.classList.remove("hidden");
  }

  function loadProfile() {
    apiFetch("/api/me/profile").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      if (!data) return;
      const nameEl = document.getElementById("profile-display-name");
      const bioEl = document.getElementById("profile-display-bio");
      if (nameEl) nameEl.textContent = data.display_name || data.username || "";
      if (bioEl) bioEl.textContent = data.bio || "";
      setProfilePictureCircle(data);
    });
  }

  function setupProfileForm() {
    const profileDisplay = document.getElementById("profile-display");
    const profileForm = document.getElementById("profile-form");
    const profileEditBtn = document.getElementById("profile-edit-btn");
    const profileCancelBtn = document.getElementById("profile-edit-cancel");
    const displayNameEl = document.getElementById("profile-display-name");
    const displayBioEl = document.getElementById("profile-display-bio");
    const inputName = document.getElementById("profile-display-name-input");
    const inputBio = document.getElementById("profile-bio-input");
    const errEl = document.getElementById("profile-error");
    const successEl = document.getElementById("profile-success");

    function showDisplay() {
      if (profileDisplay) profileDisplay.classList.remove("hidden");
      if (profileForm) profileForm.classList.add("hidden");
    }
    var selectedAvatarPath = null;

    function loadAvatarGrid() {
      const grid = document.getElementById("profile-avatar-grid");
      if (!grid) return;
      grid.innerHTML = "";
      apiFetch("/api/profile-avatars").then(function (res) {
        if (!res.ok) return res.json();
        return res.json();
      }).then(function (data) {
        const paths = (data && data.paths) || [];
        paths.forEach(function (path) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.setAttribute("aria-label", "Use avatar " + path);
          const url = staticBaseForSocialPage() + path;
          btn.innerHTML = "<img src=\"" + url + "\" alt=\"\">";
          if (selectedAvatarPath === path) btn.classList.add("selected");
          btn.addEventListener("click", function () {
            grid.querySelectorAll("button").forEach(function (b) { b.classList.remove("selected"); });
            btn.classList.add("selected");
            selectedAvatarPath = path;
            if (errEl) errEl.textContent = "";
            apiFetch("/api/me/profile", {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ avatar_path: path })
            }).then(function (res) {
              if (res.status === 401) { redirectToLogin(); return; }
              return res.json();
            }).then(function (d) {
              if (d) setProfilePictureCircle(d);
              if (successEl) successEl.textContent = "Profile picture updated.";
            }).catch(function () {
              if (errEl) errEl.textContent = "Could not set picture.";
            });
          });
          grid.appendChild(btn);
        });
      });
    }

    function showEdit() {
      if (profileDisplay) profileDisplay.classList.add("hidden");
      if (profileForm) profileForm.classList.remove("hidden");
      if (inputName && displayNameEl) inputName.value = displayNameEl.textContent;
      if (inputBio && displayBioEl) inputBio.value = displayBioEl.textContent;
      if (errEl) errEl.textContent = "";
      if (successEl) successEl.textContent = "";
      apiFetch("/api/me/profile").then(function (r) { return r.json(); }).then(function (d) {
        selectedAvatarPath = (d && d.avatar_path) || null;
        loadAvatarGrid();
      });
    }
    if (profileEditBtn) profileEditBtn.addEventListener("click", showEdit);
    if (profileCancelBtn) profileCancelBtn.addEventListener("click", showDisplay);
    if (profileForm) {
      profileForm.addEventListener("submit", function (e) {
        e.preventDefault();
        if (errEl) errEl.textContent = "";
        if (successEl) successEl.textContent = "";
        apiFetch("/api/me/profile", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            display_name: (inputName && inputName.value) ? inputName.value.trim() : null,
            bio: (inputBio && inputBio.value) ? inputBio.value.trim() : null
          })
        }).then(function (res) {
          if (res.status === 401) { redirectToLogin(); return; }
          return res.json();
        }).then(function (data) {
          if (!data) return;
          if (displayNameEl) displayNameEl.textContent = data.display_name || data.username || "";
          if (displayBioEl) displayBioEl.textContent = data.bio || "";
          setProfilePictureCircle(data);
          showDisplay();
          if (successEl) successEl.textContent = "Profile saved.";
        }).catch(function () {
          if (errEl) errEl.textContent = "Could not save profile.";
        });
      });
    }
  }

  function loadLocations() {
    return apiFetch("/api/locations").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return []; }
      return res.json();
    }).then(function (data) {
      locations = data || [];
      return locations;
    });
  }

  function loadTopFourEligible() {
    return apiFetch("/api/me/top-four-eligible").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return []; }
      return res.json();
    }).then(function (data) {
      topFourEligible = data || [];
      return topFourEligible;
    });
  }

  /** Options for one slot: eligible hikes only; same hike can't be in two slots. If current selection is eligible but in another slot, show "(remove to clear)" so user can clear this slot. */
  function getTopFourOptionsHtml(slots, slotIndex) {
    const s = slots[slotIndex];
    const currentId = s && s.trip_report_info_id != null ? Number(s.trip_report_info_id) : null;
    const usedIds = slots.map(function (x) { return x.trip_report_info_id != null ? Number(x.trip_report_info_id) : null; }).filter(function (id) { return id != null; });
    const exclude = usedIds.filter(function (id, i) { return i !== slotIndex; });
    const eligibleIds = (topFourEligible || []).map(function (loc) { return Number(loc.id); });
    const list = (topFourEligible || []).filter(function (loc) { return !exclude.includes(Number(loc.id)); });
    if (currentId && eligibleIds.indexOf(currentId) !== -1 && !list.some(function (loc) { return Number(loc.id) === currentId; }) && s.hike_name) {
      list.unshift({ id: currentId, hike_name: (s.hike_name || "").replace(/\s*\(remove to clear\)\s*$/, "") + " (remove to clear)" });
    }
    if (list.length === 0) {
      return '<option value="">' + (currentId ? "Clear slot above or write a report first" : "Write a trip report first") + '</option>';
    }
    return getLocationsOptionsHtml(list, []);
  }

  /** When true, top four cards show dropdowns to pick hike; when false, just thumb + name. */
  let topFourEditMode = false;

  function loadTopFour() {
    const errTopFour = document.getElementById("top-four-error");
    if (errTopFour) errTopFour.textContent = "";
    apiFetch("/api/me/top-four").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (slots) {
      if (!slots || !Array.isArray(slots)) return;
      const container = document.getElementById("top-four-slots");
      if (!container) return;
      if (!topFourEligible.length && !slots.some(function (s) { return s.trip_report_info_id; })) {
        container.innerHTML = "<p class=\"friends-section-desc\">Write at least one trip report below, then you can choose your top four here.</p>";
        const actions = document.querySelector(".top-four-actions");
        if (actions) actions.classList.add("hidden");
        return;
      }
      const actions = document.querySelector(".top-four-actions");
      if (actions) actions.classList.remove("hidden");
      const editBtn = document.getElementById("top-four-edit-btn");
      const editButtons = document.getElementById("top-four-edit-buttons");
      if (editBtn && editButtons) {
        if (topFourEditMode) {
          editBtn.classList.add("hidden");
          editButtons.classList.remove("hidden");
        } else {
          editBtn.classList.remove("hidden");
          editButtons.classList.add("hidden");
        }
      }
      container.innerHTML = slots.map(function (s, idx) {
        const pos = s.position || idx + 1;
        const name = (s.hike_name && s.hike_name.replace(/\s*\(remove to clear\)\s*$/, "")) || "—";
        const options = getTopFourOptionsHtml(slots, idx);
        const selectHtml = topFourEditMode
          ? '<div class="top-four-slot"><label>Hike</label><select data-slot="' + pos + '">' + options + '</select></div>'
          : "";
        const reportId = s && (s.latest_report_id || s.image_report_id) ? (s.latest_report_id || s.image_report_id) : null;
        const imgReportId = s && s.image_report_id ? s.image_report_id : null;
        const thumbInner = imgReportId
          ? '<img src="' + API_BASE + '/api/trip-reports/' + encodeURIComponent(imgReportId) + '/image" alt="' + escapeHtml(name) + ' photo" />'
          : '<span class="top-four-thumb-placeholder">Photo</span>';
        const thumb = reportId
          ? '<a class="top-four-thumb" href="trip_report_view.html?id=' + encodeURIComponent(reportId) + '" aria-label="View trip report for ' + escapeHtml(name) + '">' + thumbInner + '</a>'
          : '<div class="top-four-thumb" aria-label="Hike photo slot ' + pos + '">' + thumbInner + '</div>';
        return '<div class="top-four-card">' +
          thumb +
          '<p class="top-four-name">' + escapeHtml(name) + '</p>' +
          selectHtml +
          '</div>';
      }).join("");
      slots.forEach(function (s, idx) {
        const pos = s.position || idx + 1;
        const sel = container.querySelector('select[data-slot="' + pos + '"]');
        if (sel && s.trip_report_info_id) sel.value = String(s.trip_report_info_id);
      });
      if (topFourEditMode) {
        container.querySelectorAll("select[data-slot]").forEach(function (sel) {
          sel.addEventListener("change", saveTopFour);
        });
      }
    });
  }

  function saveTopFour() {
    const container = document.getElementById("top-four-slots");
    if (!container) return;
    const slots = [];
    container.querySelectorAll("select[data-slot]").forEach(function (sel) {
      const pos = parseInt(sel.getAttribute("data-slot"), 10);
      const val = sel.value ? parseInt(sel.value, 10) : null;
      if (val) slots.push({ position: pos, trip_report_info_id: val });
    });
    const errTopFour = document.getElementById("top-four-error");
    if (errTopFour) errTopFour.textContent = "";
    apiFetch("/api/me/top-four", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slots: slots })
    }).then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      if (res.ok) {
        topFourEditMode = false;
        loadTopFour();
        return;
      }
      return res.json().then(function (data) {
        if (errTopFour && data && data.error) errTopFour.textContent = data.error;
      });
    });
  }

  function setupTopFourEdit() {
    const editBtn = document.getElementById("top-four-edit-btn");
    const saveBtn = document.getElementById("top-four-save-btn");
    const cancelBtn = document.getElementById("top-four-cancel-btn");
    if (editBtn) {
      editBtn.addEventListener("click", function () {
        topFourEditMode = true;
        loadTopFour();
      });
    }
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        saveTopFour();
      });
    }
    if (cancelBtn) {
      cancelBtn.addEventListener("click", function () {
        topFourEditMode = false;
        loadTopFour();
      });
    }
  }

  function loadFriendRequests() {
    apiFetch("/api/friends/requests").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      const el = document.getElementById("friend-requests-list");
      if (!el) return;
      if (!data || data.length === 0) {
        el.innerHTML = "<p class=\"friends-section-desc\">No pending requests.</p>";
        return;
      }
      el.innerHTML = data.map(function (r) {
        return '<div class="friend-request-item" data-request-id="' + r.id + '">' +
          '<span>' + escapeHtml(r.sender_username) + '</span> ' +
          '<button type="button" class="secondary accept-request" data-request-id="' + r.id + '">Accept</button> ' +
          '<button type="button" class="secondary decline-request" data-request-id="' + r.id + '">Decline</button>' +
          '</div>';
      }).join("");
      el.querySelectorAll(".accept-request").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-request-id");
          apiFetch("/api/friends/requests/" + id + "/accept", { method: "POST" }).then(function (r) {
            if (r.ok) { loadFriendRequests(); loadFriends(); }
          });
        });
      });
      el.querySelectorAll(".decline-request").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-request-id");
          apiFetch("/api/friends/requests/" + id + "/decline", { method: "POST" }).then(function (r) {
            if (r.ok) loadFriendRequests();
          });
        });
      });
    });
  }

  function loadFriends() {
    apiFetch("/api/friends").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      const el = document.getElementById("my-friends-list");
      if (!el) return;
      if (!data || data.length === 0) {
        el.innerHTML = "<p class=\"friends-section-desc\">No friends yet.</p>";
        return;
      }
      el.innerHTML = data.map(function (f) {
        const username = encodeURIComponent(f.username || "");
        return '<div class="friend-item">' +
          escapeHtml(f.username) + ' <a href="profile_view.html?username=' + username + '" class="secondary">View profile</a>' +
          '</div>';
      }).join("");
    });
  }

  function loadTripReports() {
    apiFetch("/api/me/trip-reports").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      const el = document.getElementById("my-trip-reports-list");
      if (!el) return;
      if (!data || data.length === 0) {
        el.innerHTML = "<p class=\"friends-section-desc\">No trip reports yet.</p>";
        return;
      }
      el.innerHTML = data.map(function (r) {
        const dateStr = r.date_hiked ? (r.date_hiked.slice ? r.date_hiked.slice(0, 10) : r.date_hiked) : "";
        const title = escapeHtml(r.title || "");
        const hike = escapeHtml(r.hike_name || "");
        return '<div class="trip-report-item">' +
          '<a href="trip_report_view.html?id=' + encodeURIComponent(r.id) + '"><strong>' + title + '</strong> — ' + hike + (dateStr ? " · " + dateStr : "") + '</a>' +
          '</div>';
      }).join("");
    });
  }

  function setupTripReportForm() {
    const tripReportHike = document.getElementById("trip-report-hike");
    const addWishlistSelect = document.getElementById("add-wishlist-select");
    if (tripReportHike) tripReportHike.innerHTML = getLocationsOptionsHtml(locations);
    if (addWishlistSelect) addWishlistSelect.innerHTML = getLocationsOptionsHtml(locations);

    const toggleBtn = document.getElementById("toggle-trip-report-form");
    const form = document.getElementById("trip-report-form");
    const cancelBtn = document.getElementById("trip-report-cancel");
    const errEl = document.getElementById("trip-report-form-error");
    if (toggleBtn && form) {
      toggleBtn.addEventListener("click", function () {
        form.hidden = false;
        toggleBtn.hidden = true;
        document.getElementById("trip-report-edit-id").value = "";
      });
    }
    if (cancelBtn && form && toggleBtn) {
      cancelBtn.addEventListener("click", function () {
        form.hidden = true;
        toggleBtn.hidden = false;
      });
    }
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (errEl) errEl.textContent = "";
        const hikeId = document.getElementById("trip-report-hike").value;
        const title = document.getElementById("trip-report-title").value.trim();
        const body = document.getElementById("trip-report-body").value.trim();
        const dateHiked = document.getElementById("trip-report-date").value || null;
        if (!hikeId || !title) {
          if (errEl) errEl.textContent = "Please choose a hike and enter a title.";
          return;
        }
        apiFetch("/api/me/trip-reports", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            trip_report_info_id: parseInt(hikeId, 10),
            title: title,
            body: body,
            date_hiked: dateHiked || null
          })
        }).then(function (res) {
          if (res.status === 401) { redirectToLogin(); return; }
          return res.json();
        }).then(function (data) {
          if (data) {
            form.hidden = true;
            if (toggleBtn) toggleBtn.hidden = false;
            form.reset();
            loadTripReports();
            loadTopFourEligible().then(function () { loadTopFour(); });
          }
        }).catch(function () {
          if (errEl) errEl.textContent = "Could not save report.";
        });
      });
    }
  }

  function loadWishlist() {
    apiFetch("/api/me/wishlist").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      const el = document.getElementById("my-wishlist-list");
      if (!el) return;
      if (!data || data.length === 0) {
        el.innerHTML = "<p class=\"friends-section-desc\">No hikes on your wishlist yet.</p>";
        return;
      }
      el.innerHTML = data.map(function (w) {
        return '<div class="favorite-item" data-id="' + w.id + '">' +
          escapeHtml(w.hike_name || "") +
          ' <button type="button" class="secondary remove-wishlist" data-id="' + w.id + '">Remove</button>' +
          '</div>';
      }).join("");
      el.querySelectorAll(".remove-wishlist").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const id = btn.getAttribute("data-id");
          apiFetch("/api/me/wishlist/" + id, { method: "DELETE" }).then(function (r) {
            if (r.ok) { loadWishlist(); refreshWishlistDropdown(); }
          });
        });
      });
    });
  }

  function refreshWishlistDropdown() {
    apiFetch("/api/me/wishlist").then(function (res) { return res.json(); }).then(function (wishlist) {
      const ids = (wishlist || []).map(function (w) { return w.id; });
      const sel = document.getElementById("add-wishlist-select");
      if (sel) sel.innerHTML = getLocationsOptionsHtml(locations, ids);
    });
  }

  function setupSearchUser() {
    const form = document.getElementById("search-user-form");
    const input = document.getElementById("search-user-input");
    const errEl = document.getElementById("search-user-error");
    if (!form || !input) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (errEl) errEl.textContent = "";
      const username = (input.value || "").trim();
      if (!username) {
        if (errEl) errEl.textContent = "Enter a username.";
        return;
      }
      apiFetch("/api/users/" + encodeURIComponent(username) + "/profile").then(function (res) {
        if (res.status === 401) { redirectToLogin(); return; }
        if (res.status === 404) {
          if (errEl) errEl.textContent = "User not found.";
          return;
        }
        if (res.ok) {
          window.location.href = "profile_view.html?username=" + encodeURIComponent(username);
        }
      });
    });
  }

  function setupAddWishlist() {
    const btn = document.getElementById("add-wishlist-btn");
    const sel = document.getElementById("add-wishlist-select");
    const errEl = document.getElementById("add-wishlist-error");
    if (!btn || !sel) return;
    btn.addEventListener("click", function () {
      if (errEl) errEl.textContent = "";
      const id = sel.value;
      if (!id) {
        if (errEl) errEl.textContent = "Choose a hike.";
        return;
      }
      apiFetch("/api/me/wishlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trip_report_info_id: parseInt(id, 10) })
      }).then(function (res) {
        if (res.status === 401) { redirectToLogin(); return; }
        if (res.ok) {
          loadWishlist();
          refreshWishlistDropdown();
          sel.value = "";
        } else {
          return res.json();
        }
      }).then(function (data) {
        if (data && data.error && errEl) errEl.textContent = data.error;
      });
    });
  }

  function init() {
    apiFetch("/api/me").then(function (res) {
      if (res.status === 401) {
        redirectToLogin();
        return;
      }
      loadProfile();
      loadFriendRequests();
      loadFriends();
      loadTripReports();
      loadWishlist();
      loadLocations().then(function () {
        setupTripReportForm();
        refreshWishlistDropdown();
      });
      loadTopFourEligible().then(function () {
        loadTopFour();
      });
      setupTopFourEdit();
      setupProfileForm();
      setupSearchUser();
      setupAddWishlist();
      initNav();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
