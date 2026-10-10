// The end of the easter-egg trail: X marks the spot. Typing "xxx" (or the Konami code)
// anywhere outside a text box finds the treasure, which unlocks the Moka Pot Magic color
// themes for good.
//
// Finding it saves "treasure" = "found" in localStorage and sets data-treasure="found" on
// <html> (the inline script in base.html restores that before first paint), which CSS
// uses to reveal everything marked .treasure-only: the themes in the gear menu and a 💰
// trophy in the footer.
(function () {
  const root = document.documentElement;
  const SECRETS = [
    ["x", "x", "x"],
    ["arrowup", "arrowup", "arrowdown", "arrowdown"]
      .concat(["arrowleft", "arrowright", "arrowleft", "arrowright", "b", "a"]),
  ];
  const longest = Math.max(...SECRETS.map((s) => s.length));
  let recent = [];

  function typing(target) {
    return target.closest("input, textarea, select, [contenteditable]:not([contenteditable=false])");
  }

  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || typing(e.target)) return;
    recent = recent.concat(e.key.toLowerCase()).slice(-longest);
    const hit = SECRETS.some((s) => s.every((key, i) => recent[recent.length - s.length + i] === key));
    if (hit) {
      recent = [];
      find();
    }
  });

  function find() {
    const already = root.dataset.treasure === "found";
    root.dataset.treasure = "found";
    try {
      localStorage.setItem("treasure", "found");
    } catch (e) {
      // Storage blocked: the treasure still shows on this page.
    }
    celebrate(already);
  }

  function el(tag, props = {}, children = []) {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
  }

  function celebrate(already) {
    if (document.querySelector(".treasure-dialog")) return;
    const close = el("button", { className: "button", type: "button", textContent: "Close" });
    const open = el("button", {
      className: "button button-solid",
      type: "button",
      textContent: "Open the color menu",
    });
    const dialog = el("dialog", { className: "treasure-dialog" }, [
      el("div", { className: "treasure-art" }, [
        el("span", { className: "treasure-x", textContent: "❌" }),
        el("span", { className: "treasure-chest", textContent: "💰" }),
      ]),
      el("h2", {
        textContent: already ? "Back for more gold?" : "You found the gold, adventurer!",
      }),
      el("p", {
        textContent:
          "The Moka Pot Magic collection is yours: color themes drawn from my art " +
          "series. Find them in the color menu (the gear, top right).",
      }),
      el("div", { className: "treasure-actions" }, [open, close]),
    ]);
    dialog.querySelector(".treasure-art").setAttribute("aria-hidden", "true");
    dialog.setAttribute("aria-labelledby", "treasure-title");
    dialog.querySelector("h2").id = "treasure-title";

    close.addEventListener("click", () => dialog.close());
    open.addEventListener("click", (e) => {
      // Keep this click from reaching theme.js's outside-click handler, which would
      // close the menu right after it opens.
      e.stopPropagation();
      dialog.close();
      const toggle = document.querySelector(".settings-toggle");
      if (toggle && toggle.getAttribute("aria-expanded") !== "true") toggle.click();
      document.querySelector(".treasure-only .palette-option")?.focus();
    });
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) dialog.close(); // a click on the backdrop
    });
    dialog.addEventListener("close", () => dialog.remove());

    document.body.append(dialog);
    dialog.showModal();
    console.log("%c💰 Treasure found. Well sailed, adventurer.", "font-size: 1.2em; font-weight: 700;");
  }
})();
