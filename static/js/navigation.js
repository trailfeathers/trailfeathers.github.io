/**
 * Global navigation: home, back to trips.
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
