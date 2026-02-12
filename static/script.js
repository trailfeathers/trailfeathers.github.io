const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

document.addEventListener("DOMContentLoaded", () => {
  // First Page buttons
  const loginButton = document.querySelector("#login");
  const registerButton = document.querySelector("#register");

  if (loginButton) {
    loginButton.addEventListener("click", () => {
      window.location.href = "static/login.html";
    });
  }

  if (registerButton) {
    registerButton.addEventListener("click", () => {
      window.location.href = "static/register.html";
    });
  }

  // Back button (Login Page)
  const backButtonLogin = document.querySelector("#back-button-login");
  if (backButtonLogin) {
    backButtonLogin.addEventListener("click", () => {
      window.history.back();
    });
  }

  // Login Form – call API, then redirect or show error
  const loginForm = document.querySelector("#login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.querySelector("#login-form #username").value.trim();
      const password = document.querySelector("#login-form #password").value;
      const errEl = document.querySelector("#login-error");
      if (errEl) errEl.textContent = "";

      if (!username || !password) {
        if (errEl) errEl.textContent = "Please enter username and password.";
        return;
      }

      try {
        const res = await fetch(API_BASE + "/api/login", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        if (res.ok) {
          window.location.href = "dashboard.html";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Invalid credentials.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  // Registration Form – validate confirm password, call API, then redirect or show error
  const registerForm = document.querySelector("#register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.querySelector("#register-form #username").value.trim();
      const password = document.querySelector("#register-form #password").value;
      const confirmPassword = document.querySelector("#register-form #confirm-password").value;
      const errEl = document.querySelector("#register-error");
      if (errEl) errEl.textContent = "";

      if (!username || !password) {
        if (errEl) errEl.textContent = "Please enter username and password.";
        return;
      }
      if (password !== confirmPassword) {
        if (errEl) errEl.textContent = "Passwords don't match.";
        return;
      }

      try {
        const res = await fetch(API_BASE + "/api/signup", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        if (res.ok) {
          window.location.href = "dashboard.html";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) {
          if (errEl) errEl.textContent = "Username already exists.";
        } else {
          if (errEl) errEl.textContent = data.error || "Something went wrong. Try again.";
        }
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }

  // Back button (Registration Page)
  const backButtonRegister = document.querySelector("#back-button-register");
  if (backButtonRegister) {
    backButtonRegister.addEventListener("click", () => {
      window.history.back();
    });
  }

  // Dashboard buttons
  const inventory = document.querySelector("#inventory");
  if (inventory) inventory.addEventListener("click", () => (window.location.href = "inventory.html"));
  const planTrip = document.querySelector("#plan-trip");
  if (planTrip) planTrip.addEventListener("click", () => (window.location.href = "trip.html"));
  const addFriend = document.querySelector("#add-friend");
  if (addFriend) addFriend.addEventListener("click", () => (window.location.href = "friends.html"));
  const home = document.querySelector("#home");
  if (home) home.addEventListener("click", () => (window.location.href = "dashboard.html"));

  // ---------- Inventory: load gear and add form ----------
  const inventoryTable = document.querySelector("#inventory-table");
  const addItemForm = document.querySelector("#add-item-form");

  async function loadGear() {
    if (!inventoryTable) return;
    try {
      const res = await fetch(API_BASE + "/api/gear", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        inventoryTable.innerHTML = "<tr><td colspan=\"7\">Could not load gear.</td></tr>";
        return;
      }
      const items = await res.json();
      if (items.length === 0) {
        inventoryTable.innerHTML = "<tr><td colspan=\"7\">No gear yet. Add some below.</td></tr>";
        return;
      }
      inventoryTable.innerHTML = items
        .map(
          (item) =>
            `<tr>
              <td>${escapeHtml(item.type || "—")}</td>
              <td>${escapeHtml(item.name || "—")}</td>
              <td>${escapeHtml(item.capacity != null ? String(item.capacity) : "—")}</td>
              <td>${item.weight_oz != null ? item.weight_oz : "—"}</td>
              <td>${escapeHtml(item.brand || "—")}</td>
              <td>${escapeHtml(item.condition || "—")}</td>
              <td>${escapeHtml(item.notes || "—")}</td>
            </tr>`
        )
        .join("");
    } catch (_) {
      inventoryTable.innerHTML = "<tr><td colspan=\"7\">Could not load gear.</td></tr>";
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  if (inventoryTable) loadGear();

  if (addItemForm) {
    addItemForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errEl = document.querySelector("#add-gear-error");
      if (errEl) errEl.textContent = "";

      const name = document.querySelector("#gear-name").value.trim();
      if (!name) {
        if (errEl) errEl.textContent = "Name is required.";
        return;
      }

      const payload = {
        type: (document.querySelector("#gear-type").value || "other").trim() || "other",
        name,
        capacity: document.querySelector("#gear-capacity").value.trim() || undefined,
        brand: document.querySelector("#gear-brand").value.trim() || undefined,
        condition: document.querySelector("#gear-condition").value.trim() || undefined,
        notes: document.querySelector("#gear-notes").value.trim() || undefined,
      };
      const weightVal = document.querySelector("#gear-weight").value;
      if (weightVal !== "" && weightVal != null) {
        const w = parseFloat(weightVal);
        if (!Number.isNaN(w) && w >= 0) payload.weight_oz = w;
      }

      try {
        const res = await fetch(API_BASE + "/api/gear", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          addItemForm.reset();
          document.querySelector("#gear-type").value = "other";
          loadGear();
          if (errEl) errEl.textContent = "";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (errEl) errEl.textContent = data.error || "Could not add gear.";
      } catch (_) {
        if (errEl) errEl.textContent = "Could not reach the server. Try again later.";
      }
    });
  }
});

// Inventory nav (when already on page)
const home = document.querySelector("#home");
if (home) {
  home.addEventListener("click", () => {
    window.location.href = "dashboard.html";
  });
}

// Trip Planner

// Friends