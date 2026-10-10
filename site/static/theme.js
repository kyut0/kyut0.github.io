// Color theme menu (gear icon): one list of every theme in both modes, e.g. "Ember (dark)".
//
// A choice saves two things in localStorage: "theme" (light or dark) and "palette" (the
// theme name; cleared for the default theme, so a renamed default never strands anyone).
// The inline script in base.html applies both before first paint. Until a visitor picks,
// they get the default theme in their system's light or dark mode, following it live.
(function () {
  const root = document.documentElement;
  const toggle = document.querySelector(".settings-toggle");
  const menu = document.getElementById("settings-menu");
  if (!toggle || !menu) return;
  const options = [...menu.querySelectorAll(".palette-option")];
  const defaultPalette = options.find((o) => o.dataset.default === "true")?.dataset.palette;

  const store = {
    get(key) {
      try {
        return localStorage.getItem(key);
      } catch (e) {
        return null; // storage blocked (private mode, etc.)
      }
    },
    set(key, value) {
      try {
        if (value === null) localStorage.removeItem(key);
        else localStorage.setItem(key, value);
      } catch (e) {
        // Storage blocked: the choice still applies to this page.
      }
    },
  };

  function sync() {
    const palette = root.dataset.palette || defaultPalette;
    for (const option of options) {
      const on = option.dataset.palette === palette && option.dataset.mode === root.dataset.theme;
      option.setAttribute("aria-pressed", String(on));
    }
  }

  function setOpen(open) {
    menu.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  }

  toggle.addEventListener("click", () => setOpen(menu.hidden));

  menu.addEventListener("click", (e) => {
    const option = e.target.closest(".palette-option");
    if (!option) return;
    const isDefault = option.dataset.default === "true";
    root.dataset.theme = option.dataset.mode;
    if (isDefault) delete root.dataset.palette;
    else root.dataset.palette = option.dataset.palette;
    store.set("theme", option.dataset.mode);
    store.set("palette", isDefault ? null : option.dataset.palette);
    sync();
  });

  document.addEventListener("click", (e) => {
    if (!menu.hidden && !e.target.closest(".settings")) setOpen(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !menu.hidden) {
      setOpen(false);
      toggle.focus();
    }
  });

  // Until the visitor picks, keep following their system's light/dark setting.
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
    const saved = store.get("theme");
    if (saved === "light" || saved === "dark") return;
    root.dataset.theme = e.matches ? "light" : "dark";
    sync();
  });

  sync();
  toggle.hidden = false;
})();
