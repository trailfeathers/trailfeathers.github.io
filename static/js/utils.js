/**
 * TrailFeathers - Shared utility functions (escapeHtml, getWeatherIcon, loadUserSession, loadUserInfo).
 * Group: TrailFeathers
 * Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
 * Last updated: 3/13/26
 */

/**
 * Escapes a string for safe insertion into HTML (avoids XSS when setting innerHTML).
 * @param {string} text - Raw string (e.g. user input or API data)
 * @returns {string} HTML-escaped string
 */
export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Maps NWS shortForecast string to a weather icon filename (no extension).
 * Used on the trip dashboard to pick an image from images_for_site/weather_icons/.
 * @param {string} shortForecast - e.g. "Partly Sunny" or "Rain"
 * @returns {string} Icon name: sunny, partly_cloudy, rain, snow, windy, fog, etc.
 */
export function getWeatherIcon(shortForecast) {
  if (!shortForecast || typeof shortForecast !== "string") return "partly_cloudy";
  const s = shortForecast.toLowerCase();
  if (/snow/.test(s)) return "snow";
  if (/rain|shower|thunder/.test(s)) return "rain";
  if (/wind/.test(s)) return "windy";
  if (/fog|haze/.test(s)) return "fog";
  if (/(^|\s)sunny|clear/.test(s) && !/partly|mostly/.test(s)) return "sunny";
  if (/partly|cloudy|mostly/.test(s)) return "partly_cloudy";
  return "partly_cloudy";
}
