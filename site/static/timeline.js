// Resume timeline: click a tool to trace it through every step that used it, toggle
// event types on and off, and fade events in as they scroll into view. Without
// JavaScript the full timeline still renders; only these extras are missing.
(function () {
  const timeline = document.querySelector(".timeline");
  if (!timeline) return;

  const events = [...timeline.querySelectorAll(".tl-event")];
  const years = [...timeline.querySelectorAll(".tl-year")];
  const controls = document.querySelector(".timeline-controls");
  const status = controls.querySelector(".tl-status");
  const statusText = status.querySelector(".tl-status-text");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let activeSkill = null;
  const hiddenKinds = new Set();

  const usesSkill = (event, key) => event.dataset.skills.split(" ").includes(key);

  function render() {
    let matches = 0;
    for (const event of events) {
      event.hidden = hiddenKinds.has(event.dataset.kind);
      const match = !activeSkill || usesSkill(event, activeSkill);
      event.classList.toggle("is-dimmed", !match);
      if (activeSkill && match && !event.hidden) matches++;
    }
    // Hide a year marker when every event in that year is filtered out.
    for (const year of years) {
      year.hidden = events.every((e) => e.dataset.year !== year.dataset.year || e.hidden);
    }
    for (const chip of document.querySelectorAll(".chip[data-skill]")) {
      const on = chip.dataset.skill === activeSkill;
      chip.classList.toggle("is-active", on);
      chip.setAttribute("aria-pressed", String(on));
    }
    status.hidden = !activeSkill;
    if (activeSkill) {
      const label = document.querySelector(`.chip[data-skill="${activeSkill}"]`).dataset.label;
      statusText.textContent = `Tracing ${label}: ${matches} step${matches === 1 ? "" : "s"}`;
    }
  }

  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip[data-skill]");
    if (chip) {
      activeSkill = activeSkill === chip.dataset.skill ? null : chip.dataset.skill;
      render();
      // From the toolbox, jump down to the first step that used the tool.
      if (activeSkill && chip.closest(".toolbox")) {
        const first = events.find((ev) => !ev.hidden && usesSkill(ev, activeSkill));
        first?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
      }
      return;
    }
    const kind = e.target.closest("[data-kind-toggle]");
    if (kind) {
      const key = kind.dataset.kindToggle;
      if (hiddenKinds.has(key)) hiddenKinds.delete(key);
      else hiddenKinds.add(key);
      kind.setAttribute("aria-pressed", String(!hiddenKinds.has(key)));
      render();
      return;
    }
    if (e.target.closest(".tl-clear")) {
      activeSkill = null;
      render();
    }
  });

  controls.hidden = false;

  // Fade events in as they scroll into view. Only events starting below the fold are
  // hidden at load, so nothing already on screen flickers.
  if (!reduceMotion && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.remove("will-reveal");
            observer.unobserve(entry.target);
          }
        }
      },
      { rootMargin: "0px 0px -10% 0px" }
    );
    for (const event of events) {
      if (event.getBoundingClientRect().top > window.innerHeight) {
        event.classList.add("will-reveal");
        observer.observe(event);
      }
    }
  }
})();
