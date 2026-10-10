// Email links (the footer's, and the sidebar's logo) copy the address instead of opening
// a mail app, and say "Copied!" for a moment. If the clipboard is unavailable, they fall
// back to mailto.
(function () {
  const links = document.querySelectorAll("a[data-copy-email]");
  if (!links.length || !navigator.clipboard) return;
  const status = document.querySelector("[data-copy-status]");

  for (const link of links) {
    const label = link.textContent;
    const isText = link.children.length === 0;
    let timer;

    link.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await navigator.clipboard.writeText(link.dataset.copyEmail);
      } catch {
        window.location.href = link.href;
        return;
      }
      if (isText) link.textContent = "Copied!";
      link.classList.add("is-copied");
      if (status) status.textContent = `Copied ${link.dataset.copyEmail}`;
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (isText) link.textContent = label;
        link.classList.remove("is-copied");
        if (status) status.textContent = "";
      }, 2000);
    });
  }
})();
