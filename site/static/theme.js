// Light/dark toggle. By default the site follows the visitor's system setting
// (prefers-color-scheme); clicking the toggle saves an explicit choice in localStorage.
// The inline script in base.html applies either one before first paint.
(function () {
  const root = document.documentElement;
  const button = document.querySelector(".theme-toggle");
  if (!button) return;

  const current = () => (root.dataset.theme === "light" ? "light" : "dark");

  function sync() {
    const next = current() === "dark" ? "light" : "dark";
    button.setAttribute("aria-label", `Switch to ${next} mode`);
    button.title = `Switch to ${next} mode`;
  }

  button.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch (e) {
      // Storage blocked (private mode, etc.): the toggle still works for this page.
    }
    sync();
  });

  // Until the visitor picks a theme, keep following their system if it changes.
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
    let saved = null;
    try {
      saved = localStorage.getItem("theme");
    } catch (err) {
      // Storage blocked: treat as no saved choice.
    }
    if (saved === "light" || saved === "dark") return;
    root.dataset.theme = e.matches ? "light" : "dark";
    sync();
  });

  sync();
  button.hidden = false;
})();
