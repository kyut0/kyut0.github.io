// Light/dark toggle. Dark is the default; a visitor's choice is saved in localStorage
// and applied before first paint by the inline script in base.html.
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

  sync();
  button.hidden = false;
})();
