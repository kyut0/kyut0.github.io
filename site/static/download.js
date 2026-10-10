// Name PDF downloads with the visitor's own date (e.g. YutK_Resume_20261009.pdf),
// set at click time. Without JavaScript the build-date name in the HTML is used.
// Also closes the Download dropdown on a pick, an outside click, or Escape.
(function () {
  const pad = (n) => String(n).padStart(2, "0");
  const menu = document.querySelector(".download-menu");

  for (const link of document.querySelectorAll("a[data-download-stem]")) {
    link.addEventListener("click", () => {
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
