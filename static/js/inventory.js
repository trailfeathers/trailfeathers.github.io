/**
 * Gear library (inventory) page: load gear by category, add form, edit panel.
 */
import { API_BASE, REQUIREMENT_KEY_TO_CATEGORY, GEAR_CATEGORY_ORDER } from "./config.js";
import { escapeHtml } from "./utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const gearCategoriesEl = document.querySelector("#gear-categories");
  const gearLoadingEl = document.querySelector("#gear-loading");
  const addItemForm = document.querySelector("#add-item-form");
  let gearEditMode = false;
  let lastGearItems = [];

  function getCategoryForKey(key) {
    if (!key) return "Other";
    return REQUIREMENT_KEY_TO_CATEGORY[key] || "Other";
  }

  function renderGearList(items) {
    if (!gearCategoriesEl || items.length === 0) return;
    const byCategory = {};
    for (const item of items) {
      const key = item.requirement_key || null;
      const cat = getCategoryForKey(key);
      if (!byCategory[cat]) byCategory[cat] = [];
      byCategory[cat].push(item);
    }
    const order = GEAR_CATEGORY_ORDER.filter((c) => byCategory[c] && byCategory[c].length > 0);
    const html = order
      .map((category) => {
        const listItems = byCategory[category]
          .map((item) => {
            const typeLabel = item.requirement_display_name || item.type || "—";
            const coversLabel = item.capacity_persons != null ? `${item.capacity_persons} people` : "Group";
            const meta = [item.capacity ? `Capacity: ${escapeHtml(String(item.capacity))}` : null, coversLabel, item.weight_oz != null ? `${item.weight_oz} oz` : null, item.brand ? escapeHtml(item.brand) : null].filter(Boolean).join(" · ");
            const liClass = gearEditMode ? "gear-category-item gear-item-editable" : "gear-category-item";
            const dataId = gearEditMode ? ` data-gear-id="${item.id}"` : "";
            const deleteBtn = gearEditMode ? `<button type="button" class="btn-delete-gear" data-gear-id="${item.id}" title="Delete this item">×</button>` : "";
            return `<li class="${liClass}"${dataId}><span class="gear-item-content"><strong>${escapeHtml(typeLabel)}</strong>: ${escapeHtml(item.name || "—")}${item.condition || item.notes ? ` <span class="gear-meta">${[item.condition, item.notes].filter(Boolean).map(escapeHtml).join(" — ")}</span>` : ""}${meta ? ` <span class="gear-meta">${meta}</span>` : ""}</span>${deleteBtn}</li>`;
          })
          .join("");
        return `<div class="gear-category-section"><h3>${escapeHtml(category)}</h3><ul>${listItems}</ul></div>`;
      })
      .join("");
    gearCategoriesEl.innerHTML = html;

    if (gearEditMode) {
      gearCategoriesEl.querySelectorAll(".btn-delete-gear").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const id = btn.getAttribute("data-gear-id");
          if (!id) return;
          if (!confirm("Delete this item? This cannot be undone.")) return;
          try {
            const r = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(id), {
              method: "DELETE",
              credentials: "include"
            });
            if (r.ok) {
              loadGear();
            }
          } catch (_) {}
        });
      });
    }

    if (gearEditMode) {
      gearCategoriesEl.querySelectorAll(".gear-item-editable").forEach((el) => {
        el.addEventListener("click", () => {
          const id = el.getAttribute("data-gear-id");
          if (id) openEditGearPanel(id);
        });
      });
    }
  }

  async function loadGear() {
    if (!gearCategoriesEl) return;
    try {
      if (gearLoadingEl) gearLoadingEl.textContent = "Loading…";
      const res = await fetch(API_BASE + "/api/gear", { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) {
        if (gearLoadingEl) gearLoadingEl.remove();
        gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">Could not load gear.</p>";
        return;
      }
      const items = await res.json();
      lastGearItems = items;
      if (gearLoadingEl) gearLoadingEl.remove();
      if (items.length === 0) {
        gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">No gear yet. Add some in the form on the left.</p>";
        return;
      }
      renderGearList(items);
    } catch (_) {
      if (gearLoadingEl) gearLoadingEl.remove();
      gearCategoriesEl.innerHTML = "<p class=\"gear-loading\">Could not load gear.</p>";
    }
  }

  const editGearSection = document.querySelector("#edit-gear-section");
  const editGearForm = document.querySelector("#edit-gear-form");
  const editGearIdEl = document.querySelector("#edit-gear-id");
  const editGearNameEl = document.querySelector("#edit-gear-name");
  const editGearTypeSelect = document.querySelector("#edit-gear-type");
  const editGearCapacityEl = document.querySelector("#edit-gear-capacity");
  const editGearCapacityPersonsEl = document.querySelector("#edit-gear-capacity-persons");
  const editGearWeightEl = document.querySelector("#edit-gear-weight");
  const editGearBrandEl = document.querySelector("#edit-gear-brand");
  const editGearConditionEl = document.querySelector("#edit-gear-condition");
  const editGearNotesEl = document.querySelector("#edit-gear-notes");
  const editGearErrorEl = document.querySelector("#edit-gear-error");
  const editGearCancelBtn = document.querySelector("#edit-gear-cancel");

  async function loadEditGearTypes() {
    if (!editGearTypeSelect) return;
    try {
      const res = await fetch(API_BASE + "/api/requirement-types", { credentials: "include" });
      if (!res.ok) return;
      const types = await res.json();
      editGearTypeSelect.innerHTML = (types.length === 0 ? [] : types)
        .map((t) => `<option value="${t.id}">${escapeHtml(t.display_name)}</option>`)
        .join("") || "<option value=\"\">Other</option>";
    } catch (_) {}
  }

  function closeEditGearPanel() {
    if (editGearSection) editGearSection.style.display = "none";
    if (editGearErrorEl) editGearErrorEl.textContent = "";
  }

  async function openEditGearPanel(gearId) {
    if (!editGearSection || !editGearForm) return;
    if (editGearErrorEl) editGearErrorEl.textContent = "";
    try {
      const res = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(gearId), { credentials: "include" });
      if (!res.ok) return;
      const item = await res.json();
      await loadEditGearTypes();
      if (editGearIdEl) editGearIdEl.value = item.id;
      if (editGearNameEl) editGearNameEl.value = item.name || "";
      if (editGearCapacityEl) editGearCapacityEl.value = item.capacity || "";
      if (editGearCapacityPersonsEl) editGearCapacityPersonsEl.value = item.capacity_persons != null ? item.capacity_persons : "";
      if (editGearWeightEl) editGearWeightEl.value = item.weight_oz != null ? item.weight_oz : "";
      if (editGearBrandEl) editGearBrandEl.value = item.brand || "";
      if (editGearConditionEl) editGearConditionEl.value = item.condition || "";
      if (editGearNotesEl) editGearNotesEl.value = item.notes || "";
      if (editGearTypeSelect) {
        const rtId = item.requirement_type_id;
        const opt = Array.from(editGearTypeSelect.options).find((o) => o.value === String(rtId));
        if (opt) editGearTypeSelect.value = String(rtId);
        else if (editGearTypeSelect.options.length) editGearTypeSelect.selectedIndex = 0;
      }
      editGearSection.style.display = "block";
    } catch (_) {}
  }

  if (editGearForm) {
    editGearForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = editGearIdEl && editGearIdEl.value;
      if (!id || !editGearNameEl) return;
      if (editGearErrorEl) editGearErrorEl.textContent = "";
      const typeOption = editGearTypeSelect && editGearTypeSelect.options[editGearTypeSelect.selectedIndex];
      const requirement_type_id = typeOption && typeOption.value ? parseInt(typeOption.value, 10) : undefined;
      const typeDisplay = typeOption && typeOption.textContent ? typeOption.textContent.trim() : "Other";
      const payload = {
        type: typeDisplay,
        name: editGearNameEl.value.trim(),
        capacity: editGearCapacityEl ? editGearCapacityEl.value.trim() || undefined : undefined,
        brand: editGearBrandEl ? editGearBrandEl.value.trim() || undefined : undefined,
        condition: editGearConditionEl ? editGearConditionEl.value.trim() || undefined : undefined,
        notes: editGearNotesEl ? editGearNotesEl.value.trim() || undefined : undefined,
      };
      if (requirement_type_id && !Number.isNaN(requirement_type_id)) payload.requirement_type_id = requirement_type_id;
      if (editGearCapacityPersonsEl && editGearCapacityPersonsEl.value !== "" && editGearCapacityPersonsEl.value != null) {
        const cp = parseInt(editGearCapacityPersonsEl.value, 10);
        if (!Number.isNaN(cp) && cp >= 1) payload.capacity_persons = cp;
      }
      if (editGearWeightEl && editGearWeightEl.value !== "" && editGearWeightEl.value != null) {
        const w = parseFloat(editGearWeightEl.value);
        if (!Number.isNaN(w) && w >= 0) payload.weight_oz = w;
      }
      try {
        const r = await fetch(API_BASE + "/api/gear/" + encodeURIComponent(id), {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (r.ok) {
          closeEditGearPanel();
          loadGear();
          return;
        }
        const data = await r.json().catch(() => ({}));
        if (editGearErrorEl) editGearErrorEl.textContent = data.error || "Could not update item.";
      } catch (_) {
        if (editGearErrorEl) editGearErrorEl.textContent = "Could not reach the server.";
      }
    });
  }
  if (editGearCancelBtn) editGearCancelBtn.addEventListener("click", closeEditGearPanel);

  const editGearBtn = document.querySelector("#edit-gear-btn");
  if (editGearBtn) {
    editGearBtn.addEventListener("click", () => {
      gearEditMode = !gearEditMode;
      editGearBtn.textContent = gearEditMode ? "Done" : "Edit Gear";
      if (!gearEditMode) closeEditGearPanel();
      if (lastGearItems.length) renderGearList(lastGearItems);
    });
  }

  async function loadRequirementTypes() {
    const selectEl = document.querySelector("#gear-type");
    if (!selectEl) return;
    try {
      const res = await fetch(API_BASE + "/api/requirement-types", { credentials: "include" });
      if (res.status === 401) return;
      if (!res.ok) {
        selectEl.innerHTML = "<option value=\"\">Could not load types</option>";
        return;
      }
      const types = await res.json();
      if (types.length === 0) {
        selectEl.innerHTML = "<option value=\"\">Other (no types in DB yet)</option>";
        return;
      }
      selectEl.innerHTML = types
        .map((t) => `<option value="${t.id}">${escapeHtml(t.display_name)}</option>`)
        .join("");
    } catch (_) {
      selectEl.innerHTML = "<option value=\"\">Could not load types</option>";
    }
  }

  if (gearCategoriesEl) loadGear();
  if (document.querySelector("#gear-type")) loadRequirementTypes();

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

      const typeSelect = document.querySelector("#gear-type");
      const typeOption = typeSelect && typeSelect.options[typeSelect.selectedIndex];
      const requirement_type_id = typeOption && typeOption.value ? parseInt(typeOption.value, 10) : undefined;
      const typeDisplay = typeOption && typeOption.textContent ? typeOption.textContent.trim() : "Other";

      const payload = {
        type: typeDisplay,
        name,
        capacity: document.querySelector("#gear-capacity").value.trim() || undefined,
        brand: document.querySelector("#gear-brand").value.trim() || undefined,
        condition: document.querySelector("#gear-condition").value.trim() || undefined,
        notes: document.querySelector("#gear-notes").value.trim() || undefined,
      };
      if (requirement_type_id && !Number.isNaN(requirement_type_id)) {
        payload.requirement_type_id = requirement_type_id;
      }
      const capPersonsEl = document.querySelector("#gear-capacity-persons");
      if (capPersonsEl && capPersonsEl.value !== "" && capPersonsEl.value != null) {
        const cp = parseInt(capPersonsEl.value, 10);
        if (!Number.isNaN(cp) && cp >= 1) payload.capacity_persons = cp;
      }

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
          if (typeSelect) typeSelect.selectedIndex = 0;
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
