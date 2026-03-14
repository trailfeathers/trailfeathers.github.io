/**
 * Global navigation: home and back-to-trips links.
 *
 * Runs on any page that loads main.js and has #home or #back-to-trips (e.g. trip_dashboard, inventory).
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
