// The hidden /type page: a Monkeytype-style timed test against Katy's personal best.
//
// Words are typed one at a time into the input; a space moves on to the next word. The
// timer starts on the first keystroke. Speed is scored like Monkeytype: characters of
// correctly typed words (plus the spaces between them), divided by 5, per minute.
(function () {
  const test = document.querySelector(".type-test");
  if (!test) return;
  const board = test.querySelector(".type-board");
  const wordsBox = test.querySelector(".type-words");
  const input = test.querySelector(".type-input");
  const timer = test.querySelector(".type-timer");
  const result = test.querySelector(".type-result");
  const restart = test.querySelector(".type-restart");
  const seconds = Number(test.dataset.seconds) || 15;
  const best = Number(test.dataset.best) || null;
  const profile = test.dataset.profile;

  // Common English words, with a few of Katy's own (cats, chickens, roller derby, moka
  // pots, soil) and some treasure-hunt loot mixed in.
  const COMMON = (
    "the be of and a to in he have it that for they with as not on she at by this we you " +
    "do but from or which one would all will there say who make when can more if no man " +
    "out other so what time up go about than into could state only new year some take " +
    "come these know see use get like then first any work now may such give over think " +
    "most even find day also after way many must look before great back through long " +
    "where much should well people down own just because good each those feel seem how " +
    "high too place little world very still nation hand old life tell write become here " +
    "show house both between need mean call develop under last right move thing general " +
    "school never same another begin while number part turn real leave might want point " +
    "form off child few small since against ask late home interest large person end open " +
    "public follow during present without again hold govern around possible head " +
    "consider word program problem however lead system set order eye plan run keep face " +
    "fact group play stand increase early course change help line"
  ).split(" ");
  const SPECIAL = (
    "moose chicken derby moka coffee soil carbon map compass treasure gold island " +
    "rainbow moon solstice art paint austin sooner"
  ).split(" ");

  let words = [];
  let index = 0; // the word being typed
  let correctChars = 0; // characters (and spaces) of correctly typed words
  let typedChars = 0;
  let rightChars = 0; // typed characters that matched, for accuracy
  let started = 0;
  let tick = null;

  function pick() {
    const list = Math.random() < 0.08 ? SPECIAL : COMMON;
    return list[Math.floor(Math.random() * list.length)];
  }

  function reset() {
    clearInterval(tick);
    tick = null;
    started = 0;
    index = correctChars = typedChars = rightChars = 0;
    words = Array.from({ length: 150 }, pick);
    wordsBox.replaceChildren(
      ...words.map((w) => {
        const span = document.createElement("span");
        span.className = "type-word";
        span.textContent = w;
        return span;
      }),
    );
    wordsBox.scrollTop = 0;
    wordsBox.children[0].classList.add("is-current");
    timer.textContent = seconds;
    result.replaceChildren();
    input.value = "";
    input.disabled = false;
  }

  function matched(typed, target) {
    let n = 0;
    for (let i = 0; i < Math.min(typed.length, target.length); i++) {
      if (typed[i] === target[i]) n++;
    }
    return n;
  }

  // Keep the current word on the box's second line, so the line above stays visible.
  // (.type-words is position: relative, so offsetTop is measured from its top.)
  function follow(span) {
    const spans = [...wordsBox.children];
    const first = spans[0].offsetTop;
    const below = spans.find((s) => s.offsetTop > first);
    const line = below ? below.offsetTop - first : span.offsetHeight;
    wordsBox.scrollTop = Math.max(0, span.offsetTop - first - line);
  }

  function commit(typed) {
    const span = wordsBox.children[index];
    const target = words[index];
    const ok = typed === target;
    typedChars += Math.max(typed.length, target.length) + 1;
    rightChars += matched(typed, target) + 1;
    if (ok) correctChars += target.length + 1;
    span.classList.remove("is-current", "is-typo");
    span.classList.add(ok ? "is-correct" : "is-wrong");
    index++;
    const next = wordsBox.children[index];
    next.classList.add("is-current");
    follow(next);
  }

  function finish() {
    clearInterval(tick);
    tick = null;
    input.disabled = true;
    // Count a correctly typed last word even without its space, as Monkeytype does.
    const partial = input.value;
    if (partial && words[index].startsWith(partial)) correctChars += partial.length;
    const wpm = Math.round(correctChars / 5 / (seconds / 60));
    const accuracy = typedChars ? Math.round((rightChars / typedChars) * 100) : 0;
    show(wpm, accuracy);
    restart.focus();
  }

  function show(wpm, accuracy) {
    const line = (text) => {
      const p = document.createElement("p");
      p.textContent = text;
      return p;
    };
    const score = line(`You: ${wpm} wpm at ${accuracy}% accuracy.`);
    score.className = "type-score";
    const lines = [score];
    if (best) {
      const mine = Math.round(best);
      if (wpm > best) {
        lines.push(line(`You out-typed my ${mine} wpm! Fair winds, captain. 🏴‍☠️`));
      } else if (wpm >= best - 10) {
        lines.push(line(`So close! My best is ${mine} wpm. One more go?`));
      } else {
        lines.push(line(`My best is ${mine} wpm. The sea is wide; keep practicing. Rematch?`));
      }
    }
    if (profile) {
      const p = document.createElement("p");
      const a = document.createElement("a");
      a.href = profile;
      a.textContent = "See my Monkeytype profile";
      p.append(a);
      lines.push(p);
    }
    result.replaceChildren(...lines);
  }

  input.addEventListener("input", () => {
    if (input.disabled) return;
    if (!started) {
      started = Date.now();
      tick = setInterval(() => {
        const left = Math.max(0, seconds - Math.floor((Date.now() - started) / 1000));
        timer.textContent = left;
        if (left === 0) finish();
      }, 100);
    }
    const value = input.value;
    if (value.endsWith(" ")) {
      const typed = value.trim();
      input.value = "";
      if (typed) commit(typed); // a lone space doesn't skip a word
      return;
    }
    const span = wordsBox.children[index];
    span.classList.toggle("is-typo", !words[index].startsWith(value));
  });

  restart.addEventListener("click", () => {
    reset();
    input.focus();
  });

  board.hidden = false;
  reset();
})();
