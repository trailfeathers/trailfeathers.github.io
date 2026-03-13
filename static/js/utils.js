/**
 * Shared utility functions for TrailFeathers.
 */

export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Map NWS shortForecast string to icon name (for weather display).
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
