/**
 * TrailFeathers - Global navigation: home and back-to-trips links (#home → dashboard, #back-to-trips → trip.html).
 * Group: TrailFeathers
 * Authors: Kim, Smith, Domst, and Snider
 * Last updated: 3/13/26
 *
 * Runs on any page that loads main.js and has #home or #back-to-trips.
 * #home → dashboard.html; #back-to-trips → trip.html (trip list).
 */
document.addEventListener("DOMContentLoaded", () => {
  const home = document.querySelector("#home");
  if (home) {
    home.addEventListener("click", () => {
      window.location.href = "dashboard.html";
    });
  }

  const backToTrips = document.querySelector("#back-to-trips");
  if (backToTrips) {
    backToTrips.addEventListener("click", () => {
      window.location.href = "trip.html";
    });
  }
});
