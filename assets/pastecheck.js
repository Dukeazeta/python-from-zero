/*
  Paste-and-check: the learner runs something on their own computer, pastes what
  the terminal showed, and the page checks it. Used wherever the lesson can't see
  the learner's machine.

  Markup (pick one rule):
    <div class="pastecheck" data-regex="^Python 3\.\d+">           any pasted line matches
    <div class="pastecheck" data-lines='["Hello", "42"]'>          exact lines, in order
      <p class="ask">Paste what your terminal showed:</p>
      <p class="ok">Message when it matches.</p>
      <p class="hint">Extra help shown when it doesn't match.</p>
    </div>

  Blank lines and spaces at the ends of lines are ignored. Lines that start with a
  prompt (">", ">>>", "PS ") are ignored too, so pasting the command along with its
  output still works.
*/
(function () {
  // Windows (PS C:\...>), Python (>>>), and Mac or Linux prompts ($, %, or "folder %", "you@pc:~$").
  const PROMPT = /^(PS [^>]*>|>>>|[A-Za-z]:\\[^>]*>|[$%#] |\S+ [$%#] |\S+@\S+[^$%#]*[$%#] )/;

  function clean(text) {
    return text.replace(/\r/g, "").split("\n").map((l) => l.trim()).filter((l) => l && !PROMPT.test(l));
  }

  function setup(box, i) {
    const ask = box.querySelector(".ask");
    const ok = box.querySelector(".ok");
    const hint = box.querySelector(".hint");
    [ok, hint].forEach((el) => el && el.remove());

    const ta = document.createElement("textarea");
    ta.className = "paste";
    ta.rows = Math.max(2, box.dataset.lines ? JSON.parse(box.dataset.lines).length + 1 : 2);
    ta.spellcheck = false;
    ta.setAttribute("aria-label", ask ? ask.textContent : "Terminal output");
    ta.placeholder = "Paste here (Ctrl + V)";
    const id = "paste-" + i;
    ta.id = id;
    if (ask) { const label = document.createElement("label"); label.htmlFor = id; label.innerHTML = ask.innerHTML; ask.replaceWith(label); }

    const bar = document.createElement("div");
    bar.className = "paste-bar";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-primary";
    btn.textContent = "Check output";
    const msg = document.createElement("p");
    msg.className = "paste-msg";
    msg.setAttribute("aria-live", "polite");
    bar.append(btn);
    box.append(ta, bar, msg);

    btn.addEventListener("click", () => {
      const lines = clean(ta.value);
      let pass = false;
      let why = "";
      if (!lines.length) {
        why = "Nothing to check yet. Copy the lines from your terminal and paste them in the box.";
      } else if (box.dataset.regex) {
        const re = new RegExp(box.dataset.regex);
        pass = lines.some((l) => re.test(l));
        if (!pass) why = `None of those lines is what we're looking for (it starts with "${lines[0]}").`;
      } else if (box.dataset.lines) {
        const want = JSON.parse(box.dataset.lines);
        pass = want.length === lines.length && want.every((w, j) => w === lines[j]);
        if (!pass) {
          const j = want.findIndex((w, k) => w !== lines[k]);
          why = j < 0
            ? `Expected ${want.length} lines but found ${lines.length}.`
            : `Line ${j + 1} should be "${want[j]}" but it's "${lines[j] ?? "(missing)"}".`;
        }
      }
      box.classList.toggle("passed", pass);
      if (lines.length) document.dispatchEvent(new CustomEvent("pfz:paste", {
        detail: { lesson: document.body.dataset.lesson || "", id: box.id || "paste-" + i, pass, pasted: ta.value.slice(0, 2000), why },
      }));
      msg.className = "paste-msg " + (pass ? "right" : "wrong");
      msg.innerHTML = "";
      if (pass) msg.innerHTML = ok ? ok.innerHTML : "That matches.";
      else {
        msg.textContent = why + " ";
        if (hint && lines.length) msg.insertAdjacentHTML("beforeend", hint.innerHTML);
      }
    });
  }

  document.querySelectorAll(".pastecheck").forEach(setup);
})();
