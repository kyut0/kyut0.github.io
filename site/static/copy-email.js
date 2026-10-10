// The footer's Email link copies the address instead of opening a mail app, and says
// "Copied!" for a moment. If the clipboard is unavailable, it falls back to mailto.
(function () {
  const link = document.querySelector("a[data-copy-email]");
  if (!link || !navigator.clipboard) return;
  const status = document.querySelector("[data-copy-status]");
  const label = link.textContent;
  let timer;

  link.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await navigator.clipboard.writeText(link.dataset.copyEmail);
    } catch {
      window.location.href = link.href;
      return;
    }
    link.textContent = "Copied!";
    status.textContent = `Copied ${link.dataset.copyEmail}`;
    clearTimeout(timer);
    timer = setTimeout(() => {
      link.textContent = label;
      status.textContent = "";
    }, 2000);
  });
})();
