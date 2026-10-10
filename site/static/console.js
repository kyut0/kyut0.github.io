// Easter egg: a welcome for anyone who opens the browser's devtools console. It's the
// first breadcrumb on the trail, pointing to the hidden /type page.
(function () {
  const style = getComputedStyle(document.documentElement);
  const color = (token, fallback) => style.getPropertyValue(token).trim() || fallback;
  const heading = color("--heading", "#ff6ec7");
  const link = color("--link", "#86b6ff");
  const gold = color("--accent-2", "#f0bf3a");
  const typePage = new URL("../type.html", document.currentScript.src).href;

  console.log(
    "%cAhoy, adventurer! 🏴‍☠️",
    `color: ${heading}; font: 600 1.6em "IBM Plex Mono", monospace;`,
  );
  console.log(
    "%cWelcome to the hidden pathway. Stay on the trail of breadcrumbs to find all the " +
      "easter eggs. There is gold where %cX%c marks the spot.",
    "font-size: 1.1em; line-height: 1.6;",
    `color: ${gold}; font-weight: 700; font-size: 1.3em;`,
    "font-size: 1.1em; line-height: 1.6;",
  );
  const here = location.href.split(/[?#]/)[0] === typePage;
  console.log(
    here
      ? "%cYou've found the first trial. Fingers ready…"
      : `%cFirst breadcrumb: a true adventurer has quick fingers. Prove yours → ${typePage}`,
    `color: ${link}; font-size: 1.1em;`,
  );
})();
