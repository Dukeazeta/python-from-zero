/*
  In-browser Python exercises, powered by Pyodide (real CPython compiled to WebAssembly).
  Code runs in a background Web Worker, so an infinite loop can be stopped instead of
  freezing the page.

  Markup (the script builds the floating window around the textarea):
    <div class="canvas exercise" id="unique-id" data-file="hello.py" data-inputs='["Ada"]'>
      <div class="task">...instructions...</div>
      <textarea class="code" spellcheck="false">starter code</textarea>
      <script type="text/python" class="tests">
check("label shown to the learner", printed(), ["Hello"])
      </script>
      <script type="text/python" class="setup">class ListNode: ...</script>   (optional, runs first)
      <script type="text/python" class="solution">print("Hello")</script>   (optional)
    </div>

  data-inputs (optional) adds an "Input" box: one line per input() call.

  Test helpers available inside .tests (one test per line):
    check(label, got, expected)   passes when got == expected
    printed()                     list of lines the learner's code printed
    source()                      the learner's code as one string
    run(["a", "b"])               run the learner's code again with these input lines;
                                  returns the printed lines (an error adds "ERROR: ...")
  Names the learner's code defined (functions, variables) are available too.

  Each exercise fires a "pfz:exercise" event on document after Check/Run, which the
  course app (assets/tutor.js) records. window.PFZ.runner exposes setup() for exercises
  added later and validate() for checking generated exercises.
*/
(function () {
  const PYODIDE_VERSION = "314.0.7";
  const INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const TIME_LIMIT_MS = 6000;

  /*HARNESS-START*/
  const HARNESS = String.raw`
import io, json, traceback, contextlib, linecache, builtins

class _Inputs:
    def __init__(self, items):
        self.items = list(items)
    def __call__(self, prompt=""):
        print(prompt, end="")
        if not self.items:
            raise EOFError("input() asked for a line, but the Input box has no more lines.")
        value = str(self.items.pop(0))
        print(value)
        return value

def _format_error(e):
    tb = e.__traceback__
    while tb is not None and tb.tb_frame.f_code.co_filename != "solution.py":
        tb = tb.tb_next
    return "".join(traceback.format_exception(type(e), e, tb)).rstrip()

def _exec(src, inputs, setup=None):
    ns = {"__name__": "__main__"}
    buf = io.StringIO()
    err = None
    linecache.cache["solution.py"] = (len(src), None, src.splitlines(True), "solution.py")
    real_input = builtins.input
    builtins.input = _Inputs(inputs)
    try:
        with contextlib.redirect_stdout(buf):
            try:
                if setup:
                    exec(compile(setup, "setup.py", "exec"), ns)
                exec(compile(src, "solution.py", "exec"), ns)
            except BaseException as e:
                err = _format_error(e) or f"{type(e).__name__}: {e}"
    finally:
        builtins.input = real_input
    return ns, buf.getvalue(), err

def _session(src, inputs_json, tests, setup=None):
    # Pyodide passes JavaScript null as a JsNull object, not None.
    tests = tests if isinstance(tests, str) else None
    setup = setup if isinstance(setup, str) else None
    inputs = json.loads(inputs_json if isinstance(inputs_json, str) else "[]")
    ns, out, err = _exec(src, inputs, setup)
    res = {"out": out, "err": err, "results": None}
    if tests is not None and err is None:
        results = []
        def check(label, got, expected):
            results.append({"label": label, "ok": got == expected,
                            "got": repr(got), "expected": repr(expected)})
        def run(lines=()):
            _, o, e = _exec(src, list(lines), setup)
            printed_lines = o.splitlines()
            if e:
                printed_lines.append("ERROR: " + e.strip().splitlines()[-1])
            return printed_lines
        helpers = {"check": check, "printed": lambda: out.splitlines(),
                   "source": lambda: src, "run": run}
        for line in tests.splitlines():
            if not line.strip():
                continue
            scope = dict(ns)
            scope.update(helpers)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(line, scope)
            except BaseException as e:
                results.append({"label": line.strip(), "ok": False,
                                "error": _format_error(e) or f"{type(e).__name__}: {e}"})
        res["results"] = results
    return json.dumps(res)
`;
  /*HARNESS-END*/

  const WORKER_SRC = `
import { loadPyodide } from ${JSON.stringify(INDEX_URL + "pyodide.mjs")};
let py = null;
const ready = (async () => {
  py = await loadPyodide({ indexURL: ${JSON.stringify(INDEX_URL)} });
  py.runPython(${JSON.stringify(HARNESS)});
  self.postMessage({ type: "ready" });
})().catch((err) => self.postMessage({ type: "boot-error", error: String(err) }));
self.onmessage = async (e) => {
  const { id, src, inputs, tests, setup } = e.data;
  try {
    await ready;
    const raw = py.globals.get("_session")(src, JSON.stringify(inputs || []), tests == null ? null : tests, setup || null);
    self.postMessage({ type: "result", id, data: JSON.parse(raw) });
  } catch (err) {
    self.postMessage({ type: "result", id, data: { out: "", err: String(err), results: null } });
  }
};`;

  // ---------- Worker pool of one, restarted after a timeout ----------
  let worker = null;
  let readyPromise = null;
  let nextId = 1;
  const pending = new Map();

  function startWorker() {
    const url = URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" }));
    worker = new Worker(url, { type: "module" });
    readyPromise = new Promise((resolve, reject) => {
      worker.onmessage = (e) => {
        const m = e.data;
        if (m.type === "ready") resolve();
        else if (m.type === "boot-error") reject(new Error("Couldn't start Python. Check your internet connection, then try again."));
        else if (m.type === "result" && pending.has(m.id)) {
          const p = pending.get(m.id);
          pending.delete(m.id);
          clearTimeout(p.timer);
          p.resolve(m.data);
        }
      };
      worker.onerror = () => reject(new Error("Couldn't start Python. Check your internet connection, then try again."));
    });
    readyPromise.catch(() => { worker && worker.terminate(); worker = null; });
  }

  function restartWorker() {
    if (worker) worker.terminate();
    worker = null;
    pending.forEach((p) => clearTimeout(p.timer));
    pending.clear();
  }

  async function execute(src, inputs, tests, setup) {
    if (!worker) startWorker();
    await readyPromise;
    return new Promise((resolve) => {
      const id = nextId++;
      const timer = setTimeout(() => {
        pending.delete(id);
        restartWorker();
        resolve({ out: "", err: null, timeout: true, results: null });
      }, TIME_LIMIT_MS);
      pending.set(id, { resolve, timer });
      worker.postMessage({ id, src, inputs, tests, setup });
    });
  }

  // ---------- Helpers ----------
  const ICON_PLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 3.5v9l7-4.5z" fill="currentColor"/></svg>';
  const ICON_CHECK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const ICON_RESET = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8a4.5 4.5 0 1 0 1.4-3.3M3.5 2.5v2.75h2.75" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    } catch (_) { return null; }
  }

  // Tab, Shift+Tab and Enter behave like a code editor. Esc leaves the editor.
  function editorKeys(ta, onEdit) {
    ta.addEventListener("keydown", (e) => {
      const { selectionStart: start, selectionEnd: end, value } = ta;
      const lineStart = value.lastIndexOf("\n", start - 1) + 1;
      if (e.key === "Tab" && !e.shiftKey) {
        e.preventDefault();
        ta.setRangeText("    ", start, end, "end");
        onEdit();
      } else if (e.key === "Tab" && e.shiftKey) {
        e.preventDefault();
        const lead = value.slice(lineStart, lineStart + 4).match(/^ */)[0].length;
        if (lead) {
          ta.setRangeText("", lineStart, lineStart + lead, "preserve");
          ta.selectionStart = ta.selectionEnd = Math.max(lineStart, start - lead);
          onEdit();
        }
      } else if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const line = value.slice(lineStart, start);
        let indent = line.match(/^ */)[0];
        if (/:\s*$/.test(line)) indent += "    ";
        ta.setRangeText("\n" + indent, start, end, "end");
        onEdit();
      } else if (e.key === "Escape") {
        ta.blur();
      }
    });
  }

  function button(cls, label, icon) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn " + cls;
    b.innerHTML = icon + "<span>" + label + "</span>";
    return b;
  }

  const lessonId = () => document.body.dataset.lesson || "";
  const narrow = matchMedia("(max-width: 900px)");  // code wraps at this width (style.css)

  // ---------- One exercise ----------
  function setup(ex, index) {
    if (ex.dataset.ready) return;
    ex.dataset.ready = "1";
    const ta = ex.querySelector("textarea.code");
    const testsEl = ex.querySelector("script.tests");
    const setupEl = ex.querySelector("script.setup");
    const setupCode = setupEl ? setupEl.textContent.replace(/^\n+|\s+$/g, "") : null;
    const starter = ta.value;
    const key = "pfz-ex:" + location.pathname + "#" + (ex.id || index);
    const saved = store(key);
    if (saved !== null && saved !== undefined && !ex.dataset.noSave) ta.value = saved;

    const win = document.createElement("div");
    win.className = "window";
    const bar = document.createElement("div");
    bar.className = "titlebar";
    bar.innerHTML = `<span class="filename">${esc(ex.dataset.file || "practice.py")}</span><span class="state">${testsEl ? "Not checked yet" : "Scratchpad"}</span>`;
    const stateEl = bar.querySelector(".state");
    ta.replaceWith(win);
    ta.setAttribute("aria-label", "Python code editor for " + (ex.dataset.file || "this exercise"));
    ta.setAttribute("spellcheck", "false");
    ta.setAttribute("autocapitalize", "off");
    ta.setAttribute("autocomplete", "off");
    ta.setAttribute("autocorrect", "off");
    ta.setAttribute("enterkeyhint", "enter");
    ta.rows = Math.max(4, starter.split("\n").length + 1);

    let inputsTa = null;
    if (ex.dataset.inputs !== undefined) {
      const box = document.createElement("div");
      box.className = "inputs";
      const id = "inputs-" + (ex.id || index);
      let lines = [];
      try { lines = JSON.parse(ex.dataset.inputs || "[]"); } catch (_) {}
      box.innerHTML = `<label for="${id}">Input <span>what the person types, one line for each <code>input()</code></span></label>`;
      inputsTa = document.createElement("textarea");
      inputsTa.id = id;
      inputsTa.className = "inputs-box";
      inputsTa.rows = Math.max(1, lines.length);
      inputsTa.spellcheck = false;
      inputsTa.value = lines.join("\n");
      box.append(inputsTa);
      win.append(bar, ta, box);
    } else {
      win.append(bar, ta);
    }
    if (setupCode) {
      const d = document.createElement("details");
      d.className = "setup-code";
      d.innerHTML = `<summary>Already written for you (runs before your code)</summary><pre class="code">${esc(setupCode)}</pre>`;
      win.insertBefore(d, ta);
    }

    const toolbar = document.createElement("div");
    toolbar.className = "toolbar";
    const checkBtn = button("btn-primary", "Check", ICON_CHECK);
    const runBtn = button("btn-tool", "Run", ICON_PLAY);
    const resetBtn = button("btn-tool", "Reset", ICON_RESET);
    const status = document.createElement("span");
    status.className = "status";
    status.setAttribute("aria-live", "polite");
    status.textContent = "Ready when you are. Python starts up in the background.";
    if (testsEl) toolbar.append(checkBtn);
    toolbar.append(runBtn, resetBtn, status);

    const out = document.createElement("div");
    out.className = "console";
    out.setAttribute("aria-live", "polite");
    win.append(toolbar, out);

    // On phones and tablets long lines wrap instead of scrolling sideways, so the editor grows to fit them.
    const fit = () => {
      if (!narrow.matches) { ta.style.height = ""; return; }
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + 2 + "px";
    };
    narrow.addEventListener("change", fit);
    window.addEventListener("resize", fit);
    requestAnimationFrame(fit);

    const onEdit = () => { if (!ex.dataset.noSave) store(key, ta.value); fit(); };
    editorKeys(ta, onEdit);
    ta.addEventListener("input", onEdit);

    resetBtn.addEventListener("click", () => {
      if (ta.value !== starter && !confirm("Replace your code with the starter code? Your changes will be lost.")) return;
      ta.value = starter;
      fit();
      store(key, null);
      out.classList.remove("show");
      win.classList.remove("solved");
      stateEl.textContent = testsEl ? "Not checked yet" : "Scratchpad";
      status.textContent = "";
    });

    let attempts = 0;
    async function go(withTests) {
      runBtn.disabled = checkBtn.disabled = resetBtn.disabled = true;
      status.textContent = worker ? "Running..." : "Loading Python (a few seconds the first time)...";
      const typed = inputsTa ? inputsTa.value.replace(/\r/g, "").replace(/\n+$/, "") : "";
      const inputs = typed === "" ? [] : typed.split("\n");
      let html = "";
      let detail = null;
      try {
        // Phone keyboards turn quotes into curly ones, which Python can't read. Straighten them.
        const straight = ta.value.replace(/[“”„″]/g, '"').replace(/[‘’‚′]/g, "'");
        if (straight !== ta.value) { ta.value = straight; onEdit(); }
        const res = await execute(ta.value, inputs, withTests ? testsEl.textContent : null, setupCode);
        if (res.out) html += `<span class="label">Your code printed</span>${esc(res.out.replace(/\n$/, ""))}\n`;
        if (res.timeout) {
          html += `<span class="label">Stopped after ${TIME_LIMIT_MS / 1000} seconds</span><span class="err">Your code was still running, so it was stopped. Usually that means a loop that never ends: check that something inside the loop changes, so its condition eventually becomes False. In the algorithms lessons it can also mean your approach is too slow for the big test inputs.</span>`;
          status.textContent = "Stopped: took too long.";
          if (testsEl) { stateEl.textContent = "Not solved yet"; win.classList.remove("solved"); }
        } else if (res.err) {
          html += `<span class="label">Python stopped with an error. Read the last line first.</span><span class="err">${esc(res.err)}</span>`;
          status.textContent = "Error. Fix it and try again.";
          if (testsEl) { stateEl.textContent = "Not solved yet"; win.classList.remove("solved"); }
        } else if (withTests) {
          const results = res.results || [];
          const passed = results.filter((r) => r.ok).length;
          html += `<span class="label">Tests</span>`;
          results.forEach((r) => {
            if (r.ok) html += `<span class="pass">${esc(r.label)}</span>\n`;
            else if (r.error) html += `<span class="fail">${esc(r.label)}</span>\n<span class="detail">  ${esc(r.error).replace(/\n/g, "\n  ")}</span>\n`;
            else html += `<span class="fail">${esc(r.label)}</span>\n<span class="detail">  expected ${esc(r.expected)}\n  got      ${esc(r.got)}</span>\n`;
          });
          const all = results.length > 0 && passed === results.length;
          win.classList.toggle("solved", all);
          stateEl.textContent = all ? "Solved" : `${passed} of ${results.length} passing`;
          status.textContent = all ? "All tests pass." : "Not yet. Read the failing test, change your code, check again.";
        } else {
          if (!res.out) html += `<span class="label">Your code ran but printed nothing. Use print() to show something.</span>`;
          status.textContent = "Ran.";
        }
        if (withTests) attempts++;
        detail = {
          lesson: lessonId(),
          id: ex.id || "exercise-" + index,
          kind: withTests ? "check" : "run",
          code: ta.value,
          inputs,
          task: (ex.querySelector(".task") || {}).innerText || "",
          tests: testsEl ? testsEl.textContent.trim() : "",
          out: res.out || "",
          error: res.timeout ? "Timed out (possible infinite loop)" : (res.err || ""),
          results: res.results,
          passed: Boolean(withTests && !res.err && !res.timeout && res.results && res.results.length && res.results.every((r) => r.ok)),
          attempts,
          practice: Boolean(ex.dataset.practice),
        };
      } catch (e) {
        html = `<span class="err">${esc(e.message || e)}</span>`;
        status.textContent = "Couldn't run.";
      }
      out.innerHTML = html.trimEnd();
      out.classList.add("show");
      runBtn.disabled = checkBtn.disabled = resetBtn.disabled = false;
      if (detail) document.dispatchEvent(new CustomEvent("pfz:exercise", { detail: Object.assign(detail, { element: ex }) }));
    }

    runBtn.addEventListener("click", () => go(false));
    checkBtn.addEventListener("click", () => go(true));
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        go(Boolean(testsEl));
      }
    });
  }

  // Check that a generated exercise is sound: the solution passes and the starter doesn't.
  async function validate({ solution, starter, tests, inputs, setup }) {
    const good = await execute(solution, inputs || [], tests, setup);
    const okGood = !good.err && !good.timeout && good.results && good.results.length > 0 && good.results.every((r) => r.ok);
    if (!okGood) return false;
    const bad = await execute(starter || "", inputs || [], tests, setup);
    const starterPasses = !bad.err && !bad.timeout && bad.results && bad.results.length > 0 && bad.results.every((r) => r.ok);
    return !starterPasses;
  }

  window.PFZ = window.PFZ || {};
  window.PFZ.runner = { setup, validate };
  document.querySelectorAll(".exercise").forEach(setup);

  // Start Python in the background once the page has settled, so it's usually ready
  // by the time the first exercise is run.
  if (document.querySelector(".exercise")) {
    setTimeout(() => {
      if (!worker) { startWorker(); readyPromise.catch(() => {}); }
    }, 1500);
  }
})();
