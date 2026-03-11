/* Trip report view page: load/save via API */
(function () {
  var API_BASE = "https://trailfeathers-github-io-real.onrender.com";
  var reportId = null;
  var locations = [];
  var currentReport = null;

  function apiFetch(path, options) {
    return fetch(API_BASE + path, Object.assign({ credentials: "include" }, options || {}));
  }

  function getReportIdFromQuery() {
    var params = new URLSearchParams(window.location.search);
    var id = params.get("id");
    return id ? parseInt(id, 10) : null;
  }

  function redirectToLogin() {
    window.location.href = "../login.html";
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

  function loadReport() {
    if (!reportId) {
      document.getElementById("report-title").textContent = "No report specified";
      return Promise.resolve();
    }
    return apiFetch("/api/trip-reports/" + reportId).then(function (res) {
      if (res.status === 401) { redirectToLogin(); return; }
      if (res.status === 404) {
        document.getElementById("report-title").textContent = "Report not found";
        return;
      }
      return res.json();
    }).then(function (data) {
      if (!data) return;
      currentReport = data;
      var reportTitle = document.getElementById("report-title");
      var reportTrail = document.getElementById("report-trail");
      var displayDate = document.getElementById("display-date");
      var reportBody = document.getElementById("report-body");
      if (reportTitle) reportTitle.textContent = data.title || "";
      if (reportTrail) reportTrail.textContent = data.hike_name || "";
      if (displayDate) displayDate.textContent = data.date_hiked ? (data.date_hiked.slice ? data.date_hiked.slice(0, 10) : data.date_hiked) : "—";
      if (reportBody) reportBody.textContent = data.body || "";

      var btnEdit = document.getElementById("btn-edit-report");
      if (data.is_owner && btnEdit) btnEdit.style.display = "inline-block";

      var reportPhoto = document.getElementById("report-photo");
      var reportPlaceholder = document.getElementById("report-image-placeholder");
      if (data.image_uploaded && reportId) {
        if (reportPhoto) {
          reportPhoto.src = API_BASE + "/api/trip-reports/" + reportId + "/image";
          reportPhoto.alt = data.title || "Trip report photo";
          reportPhoto.classList.remove("hidden");
        }
        if (reportPlaceholder) reportPlaceholder.classList.add("hidden");
      } else {
        if (reportPhoto) { reportPhoto.src = ""; reportPhoto.classList.add("hidden"); }
        if (reportPlaceholder) reportPlaceholder.classList.remove("hidden");
      }

      var trailSelect = document.getElementById("edit-trail");
      if (trailSelect && locations.length) {
        trailSelect.innerHTML = '<option value="">Choose a hike…</option>' + locations.map(function (h) {
          return '<option value="' + h.id + '">' + (h.hike_name || "") + '</option>';
        }).join("");
        if (data.trip_report_info_id) trailSelect.value = String(data.trip_report_info_id);
      }
    });
  }

  function initTripReportView() {
    reportId = getReportIdFromQuery();
    var display = document.getElementById("report-display");
    var form = document.getElementById("report-edit-form");
    var reportTitle = document.getElementById("report-title");
    var reportTrail = document.getElementById("report-trail");
    var displayDate = document.getElementById("display-date");
    var reportBody = document.getElementById("report-body");
    var editTitle = document.getElementById("edit-title");
    var editTrail = document.getElementById("edit-trail");
    var editDate = document.getElementById("edit-date");
    var editBody = document.getElementById("edit-body");
    var btnEdit = document.getElementById("btn-edit-report");
    var btnCancel = document.getElementById("btn-cancel-edit");

    if (!form || !display) return;

    function showDisplay() {
      display.classList.remove("hidden");
      form.classList.add("hidden");
      if (btnEdit) btnEdit.textContent = "Edit report";
    }

    function showEdit() {
      display.classList.add("hidden");
      form.classList.remove("hidden");
      if (editTitle && reportTitle) editTitle.value = reportTitle.textContent;
      if (editTrail && currentReport && currentReport.trip_report_info_id) editTrail.value = String(currentReport.trip_report_info_id);
      if (editDate && currentReport && currentReport.date_hiked) {
        var d = currentReport.date_hiked;
        editDate.value = d.slice ? d.slice(0, 10) : d;
      } else if (editDate) editDate.value = "";
      if (editBody && reportBody) editBody.value = reportBody.textContent;
      if (btnEdit) btnEdit.textContent = "Cancel edit";
    }

    function saveReport() {
      var tripReportInfoId = editTrail && editTrail.value ? parseInt(editTrail.value, 10) : null;
      var title = editTitle && editTitle.value ? editTitle.value.trim() : "";
      var body = editBody && editBody.value ? editBody.value.trim() : "";
      var dateHiked = editDate && editDate.value ? editDate.value : null;
      var editImage = document.getElementById("edit-image");
      var imageFile = editImage && editImage.files && editImage.files[0];
      if (!reportId) return;

      function doPut() {
        return apiFetch("/api/me/trip-reports/" + reportId, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            trip_report_info_id: tripReportInfoId,
            title: title,
            body: body,
            date_hiked: dateHiked || null
          })
        }).then(function (res) {
          if (res.status === 401) { redirectToLogin(); return; }
          return res.json();
        }).then(function (data) {
          if (data) {
            currentReport = data;
            if (reportTitle) reportTitle.textContent = data.title || "";
            if (reportTrail) reportTrail.textContent = data.hike_name || "";
            if (displayDate) displayDate.textContent = data.date_hiked ? (data.date_hiked.slice ? data.date_hiked.slice(0, 10) : data.date_hiked) : "—";
            if (reportBody) reportBody.textContent = data.body || "";
            var reportPhoto = document.getElementById("report-photo");
            var reportPlaceholder = document.getElementById("report-image-placeholder");
            if (data.image_uploaded && reportId) {
              if (reportPhoto) {
                reportPhoto.src = API_BASE + "/api/trip-reports/" + reportId + "/image?t=" + Date.now();
                reportPhoto.alt = data.title || "Trip report photo";
                reportPhoto.classList.remove("hidden");
              }
              if (reportPlaceholder) reportPlaceholder.classList.add("hidden");
            } else {
              if (reportPhoto) { reportPhoto.src = ""; reportPhoto.classList.add("hidden"); }
              if (reportPlaceholder) reportPlaceholder.classList.remove("hidden");
            }
            showDisplay();
          }
        });
      }

      if (imageFile) {
        var fd = new FormData();
        fd.append("file", imageFile);
        apiFetch("/api/me/trip-reports/" + reportId + "/image", {
          method: "POST",
          body: fd
        }).then(function (res) {
          if (res.status === 401) { redirectToLogin(); return; }
          if (!res.ok) return res.json().then(function (err) { alert(err.error || "Image upload failed"); });
          return doPut();
        });
      } else {
        doPut();
      }
    }

    if (btnEdit) {
      btnEdit.addEventListener("click", function () {
        if (form.classList.contains("hidden")) showEdit();
        else showDisplay();
      });
    }
    if (btnCancel) btnCancel.addEventListener("click", showDisplay);
    if (form) form.addEventListener("submit", function (e) { e.preventDefault(); saveReport(); });

    var logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        apiFetch("/api/logout", { method: "POST" }).then(function () {
          window.location.href = "../login.html";
        });
      });
    }

    loadLocations().then(function () {
      return loadReport();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTripReportView);
  } else {
    initTripReportView();
  }
})();
