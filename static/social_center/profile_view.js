/**
 * TrailFeathers - Profile view page (profile_view.html?username=...): public profile, relationship actions.
 * Group: TrailFeathers
 * Authors: Kim, Smith, Domst, and Snider
 * Last updated: 3/13/26
 */
const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

function escapeHtml(text) {
  if (text == null) return "";
  var div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

(function () {
  function apiFetch(path, options) {
    return fetch(API_BASE + path, Object.assign({ credentials: "include" }, options || {}));
  }

  function redirectToLogin() {
    window.location.href = "../login.html";
  }

  function initLogout() {
    var logoutBtn = document.getElementById("logout-btn");
    if (!logoutBtn) return;
    logoutBtn.addEventListener("click", function () {
      apiFetch("/api/logout", { method: "POST" }).then(function () {
        window.location.href = "../login.html";
      }).catch(function () {
        window.location.href = "../login.html";
      });
    });
  }

  function getUsernameFromQuery() {
    var params = new URLSearchParams(window.location.search);
    return params.get("username") || params.get("user") || "";
  }

  var profileUsername = "";
  var profileUserId = null;
  var relationship = { status: "none", request_id: null };

  /** Fetches profile by username, fills display name/bio/avatar, Top Four cards, and trip reports list; then loadRelationship(). */
  function loadProfile() {
    var username = getUsernameFromQuery();
    if (!username) {
      document.getElementById("profile-display-name").textContent = "No user specified.";
      return;
    }
    profileUsername = username;
    document.getElementById("banner-username").textContent = "@" + username;

    apiFetch("/api/users/" + encodeURIComponent(username) + "/profile").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      if (res.status === 404) {
        document.getElementById("profile-display-name").textContent = "User not found.";
        return;
      }
      return res.json();
    }).then(function (data) {
      if (!data) return;
      profileUserId = data.user_id;
      var displayName = data.display_name || data.username || profileUsername || "";
      document.getElementById("profile-display-name").textContent = displayName;
      document.getElementById("profile-display-bio").textContent = data.bio || "";

      var bannerTitleEl = document.getElementById("banner-title");
      if (bannerTitleEl) bannerTitleEl.textContent = (displayName ? (displayName + "'s Profile") : "Profile");
      if (displayName) document.title = "TrailFeathers — " + displayName + " — Profile";

      var img = document.getElementById("profile-picture-img");
      var ph = document.getElementById("profile-picture-placeholder");
      if (img && ph) {
        if (data.avatar_path) {
          img.src = "../" + data.avatar_path;
          img.style.display = "block";
          ph.style.display = "none";
        } else {
          img.removeAttribute("src");
          img.style.display = "none";
          ph.style.display = "flex";
        }
      }

      var topFour = document.getElementById("top-four-cards");
      var list = data.top_four || [];
      if (list.length === 0) {
        topFour.innerHTML = "<p class=\"friends-section-desc\">No hikes selected.</p>";
      } else {
        topFour.innerHTML = list.map(function (h, idx) {
          var pos = (h && h.position) ? h.position : (idx + 1);
          var name = (h && h.hike_name) ? String(h.hike_name) : "—";
          var reportId = (h && (h.latest_report_id || h.image_report_id)) ? (h.latest_report_id || h.image_report_id) : null;
          var imgReportId = (h && h.image_report_id) ? h.image_report_id : null;
          var thumbInner = imgReportId
            ? '<img src="' + API_BASE + '/api/trip-reports/' + encodeURIComponent(imgReportId) + '/image" alt="' + escapeHtml(name) + ' photo" />'
            : '<span class="top-four-thumb-placeholder">Photo</span>';
          var thumb = reportId
            ? '<a class="top-four-thumb" href="trip_report_view.html?id=' + encodeURIComponent(reportId) + '" aria-label="View trip report for ' + escapeHtml(name) + '">' + thumbInner + '</a>'
            : '<div class="top-four-thumb" aria-label="Hike photo slot ' + pos + '">' + thumbInner + '</div>';
          return '<div class="top-four-card">' +
            thumb +
            '<p class="top-four-name">' + escapeHtml(name) + '</p>' +
            '</div>';
        }).join("");
      }

      var reportsList = document.getElementById("profile-trip-reports-list");
      var reports = data.trip_reports || [];
      if (reports.length === 0) {
        reportsList.innerHTML = "<p class=\"friends-section-desc\">No trip reports yet.</p>";
      } else {
        reportsList.innerHTML = reports.map(function (r) {
          var dateStr = r.date_hiked ? (r.date_hiked.slice ? r.date_hiked.slice(0, 10) : r.date_hiked) : "";
          return '<div class="trip-report-item">' +
            '<a href="trip_report_view.html?id=' + encodeURIComponent(r.id) + '"><strong>' + escapeHtml(r.title || "") + '</strong> — ' + escapeHtml(r.hike_name || "") + (dateStr ? " · " + dateStr : "") + '</a>' +
            '</div>';
        }).join("");
      }

      return loadRelationship();
    });
  }

  /** Fetches /api/users/<username>/relationship and updates relationship state; then renderRelationship(). */
  function loadRelationship() {
    if (!profileUsername) return;
    return apiFetch("/api/users/" + encodeURIComponent(profileUsername) + "/relationship").then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      return res.json();
    }).then(function (data) {
      if (!data) return;
      relationship = { status: data.status || "none", request_id: data.request_id || null };
      renderRelationship();
    });
  }

  /** Copy for each relationship status: badge text, CSS class, description, primary/secondary button labels. */
  var RELATIONSHIP_STATES = {
    self: { badge: "This is you", badgeClass: "", text: "This is your profile.", btnText: null, btnSecondary: null },
    none: { badge: "Not friends", badgeClass: "", text: "You are not friends with this user.", btnText: "Add friend", btnSecondary: null },
    pending_out: { badge: "Pending", badgeClass: "pending", text: "Friend request sent. Waiting for response.", btnText: "Cancel request", btnSecondary: null },
    pending_in: { badge: "Pending", badgeClass: "pending", text: "This user sent you a friend request.", btnText: "Accept", btnSecondary: "Decline" },
    friend: { badge: "Friend", badgeClass: "friend", text: "You are friends with this user.", btnText: "Remove friend", btnSecondary: null }
  };

  /** Updates Relationship section UI from current relationship state; hides section when status is "self". */
  function renderRelationship() {
    var s = RELATIONSHIP_STATES[relationship.status] || RELATIONSHIP_STATES.none;
    var badge = document.getElementById("relationship-badge");
    var text = document.getElementById("relationship-status-text");
    var btn = document.getElementById("btn-manage-friend");
    var btn2 = document.getElementById("btn-manage-friend-2");
    var section = document.getElementById("relationship-section");
    if (relationship.status === "self") {
      if (section) section.style.display = "none";
      return;
    }
    if (section) section.style.display = "";
    if (badge) { badge.textContent = s.badge; badge.className = "relationship-status-badge " + (s.badgeClass || ""); }
    if (text) text.textContent = s.text;
    if (btn) {
      btn.textContent = s.btnText || "";
      btn.style.display = s.btnText ? "inline-block" : "none";
    }
    if (btn2) {
      btn2.textContent = s.btnSecondary || "";
      btn2.style.display = s.btnSecondary ? "inline-block" : "none";
    }
  }

  /** Wires Add friend / Accept / Decline / Cancel request / Remove friend to the correct API calls. */
  function setupRelationshipActions() {
    var btn = document.getElementById("btn-manage-friend");
    var btn2 = document.getElementById("btn-manage-friend-2");
    if (btn) {
      btn.addEventListener("click", function () {
        if (relationship.status === "none") {
          apiFetch("/api/friends/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: profileUsername })
          }).then(function (res) {
            if (res.status === 401) { redirectToLogin(); return; }
            if (res.ok) loadRelationship();
          });
        } else if (relationship.status === "friend" && profileUserId) {
          apiFetch("/api/friends/" + profileUserId, { method: "DELETE" }).then(function (res) {
            if (res.ok) loadRelationship();
          });
        } else if (relationship.status === "pending_out" && relationship.request_id) {
          apiFetch("/api/friends/requests/" + relationship.request_id, { method: "DELETE" }).then(function (res) {
            if (res.ok) loadRelationship();
          });
        } else if (relationship.status === "pending_in" && relationship.request_id) {
          apiFetch("/api/friends/requests/" + relationship.request_id + "/accept", { method: "POST" }).then(function (res) {
            if (res.ok) loadRelationship();
          });
        }
      });
    }
    if (btn2) {
      btn2.addEventListener("click", function () {
        if (relationship.status === "pending_in" && relationship.request_id) {
          apiFetch("/api/friends/requests/" + relationship.request_id + "/decline", { method: "POST" }).then(function (res) {
            if (res.ok) loadRelationship();
          });
        }
      });
    }
  }

  /** Home, Inventory, Plan Trip bottom nav links. */
  function initNav() {
    document.getElementById("home").addEventListener("click", function () { window.location.href = "../dashboard.html"; });
    document.getElementById("inventory").addEventListener("click", function () { window.location.href = "../inventory.html"; });
    document.getElementById("plan-trip").addEventListener("click", function () { window.location.href = "../trip.html"; });
  }

  /** Entry: logout, relationship buttons, nav, then load profile (which triggers loadRelationship). */
  function init() {
    initLogout();
    setupRelationshipActions();
    initNav();
    loadProfile();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
