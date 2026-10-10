// Name PDF downloads with the visitor's own date (e.g. YutK_Resume_20261009.pdf),
// set at click time. Without JavaScript the build-date name in the HTML is used.
// Serves the PDFs drawn in the visitor's color theme: the links in the HTML are the
// default theme's, and every other theme's copies live in <themed-dir>/<theme name>/.
// Also closes the Download dropdown on a pick, an outside click, or Escape.
(function () {
  const pad = (n) => String(n).padStart(2, "0");
  const menu = document.querySelector(".download-menu");
  const themedDir = menu?.dataset.themedDir;

  for (const link of document.querySelectorAll("a[data-download-stem]")) {
    const defaultHref = link.getAttribute("href");
    link.addEventListener("click", () => {
      // theme.js sets data-palette only for a non-default theme.
      const palette = document.documentElement.dataset.palette;
      const file = defaultHref.split("/").pop();
      link.href = palette && themedDir ? `${themedDir}${palette}/${file}` : defaultHref;
      const d = new Date();
      const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
      link.download = `${link.dataset.downloadStem}_${stamp}.pdf`;
      if (menu) menu.open = false;
    });
  }

  if (!menu) return;
  document.addEventListener("click", (e) => {
    if (menu.open && !menu.contains(e.target)) menu.open = false;
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
})();
