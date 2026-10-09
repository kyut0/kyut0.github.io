// Name the resume download with the visitor's own date (e.g. YutK_Resume_20261009.pdf),
// set at click time. Without JavaScript the build-date name in the HTML is used.
(function () {
  const pad = (n) => String(n).padStart(2, "0");

  for (const link of document.querySelectorAll("a[data-download-stem]")) {
    link.addEventListener("click", () => {
      const d = new Date();
      const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
      link.download = `${link.dataset.downloadStem}_${stamp}.pdf`;
    });
  }
})();
