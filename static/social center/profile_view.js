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

  function getUsernameFromQuery() {
    var params = new URLSearchParams(window.location.search);
    return params.get("username") || params.get("user") || "";
  }

  var profileUsername = "";
  var profileUserId = null;
  var relationship = { status: "none", request_id: null };

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
      document.getElementById("profile-display-name").textContent = data.display_name || data.username || "";
      document.getElementById("profile-display-bio").textContent = data.bio || "";

      var topFour = document.getElementById("top-four-cards");
      var list = data.top_four || [];
      if (list.length === 0) {
        topFour.innerHTML = "<p class=\"friends-section-desc\">No hikes selected.</p>";
      } else {
        topFour.innerHTML = list.map(function (h) {
          return '<div class="top-four-card">' +
            '<div class="top-four-thumb"><span class="top-four-thumb-placeholder">Photo</span></div>' +
            '<p class="top-four-name">' + escapeHtml(h.hike_name || "") + '</p></div>';
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

  var RELATIONSHIP_STATES = {
    self: { badge: "This is you", badgeClass: "", text: "This is your profile.", btnText: null, btnSecondary: null },
    none: { badge: "Not friends", badgeClass: "", text: "You are not friends with this user.", btnText: "Add friend", btnSecondary: null },
    pending_out: { badge: "Pending", badgeClass: "pending", text: "Friend request sent. Waiting for response.", btnText: "Cancel request", btnSecondary: null },
    pending_in: { badge: "Pending", badgeClass: "pending", text: "This user sent you a friend request.", btnText: "Accept", btnSecondary: "Decline" },
    friend: { badge: "Friend", badgeClass: "friend", text: "You are friends with this user.", btnText: "Remove friend", btnSecondary: null }
  };

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

  function initNav() {
    document.getElementById("home").addEventListener("click", function () { window.location.href = "../dashboard.html"; });
    document.getElementById("inventory").addEventListener("click", function () { window.location.href = "../inventory.html"; });
    document.getElementById("plan-trip").addEventListener("click", function () { window.location.href = "../trip.html"; });
  }

  function init() {
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
