// Easter egg: a welcome for anyone who opens the browser's devtools console. It's the
// first breadcrumb on the trail, pointing to the hidden /type page.
(function () {
  const style = getComputedStyle(document.documentElement);
  const color = (token, fallback) => style.getPropertyValue(token).trim() || fallback;
  const heading = color("--heading", "#ff6ec7");
  const gold = color("--accent-2", "#f0bf3a");
  const bg = color("--bg", "#24120b");
  const typePage = new URL("../type.html", document.currentScript.src).href;

  console.log(
    "%cAhoy, adventurer! 🏴‍☠️",
    `color: ${heading}; font: 600 1.6em "IBM Plex Mono", monospace;`,
  );
  // One styled segment: Chrome lays each %c segment out as its own box, so styling the X
  // separately pushed "X marks the spot" onto a new line whenever the text wrapped.
  console.log(
    "%cWelcome to the hidden pathway. Stay on the trail of breadcrumbs to find all the " +
      "easter eggs. There is gold where ❌ marks the spot.",
    "font-size: 1.1em; line-height: 1.6;",
  );
  const here = location.href.split(/[?#]/)[0] === typePage;
  console.log(
    here
      ? "%cYou've found the first trial. Fingers ready…"
      : `%cFirst breadcrumb: a true adventurer has quick fingers. Prove yours → ${typePage}`,
    // A badge on the site's own background, since devtools may be dark or light: the
    // theme's heading color is contrast-checked against --bg, not against the console.
    `color: ${heading}; background: ${bg}; border-left: 4px solid ${gold}; ` +
      "padding: 6px 10px; font-size: 1.2em; font-weight: 700;",
  );
})();
