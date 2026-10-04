/*
  Connects a page to the course app (app/server.py) when it's running:
    - records exercise, quiz and terminal results as progress
    - adds a review warm-up from earlier lessons, picked by the spaced-review schedule
    - adds "Explain my mistake" to exercises that fail (AI tutor)
    - fills the Practice section with tutor-written exercises, checked by real tests
    - adds an "Ask your tutor" chat panel
    - on the home page, marks finished lessons and points "Continue" at the next one
  With the app off (for example a page opened straight from disk) the lessons still work;
  these extras just stay hidden.
*/
(function () {
  const APP_PORT = 8765;
  // Served by the course app (on this computer or a web host), not opened straight from disk.
  const onApp = location.protocol.startsWith("http");
  const lesson = document.body.dataset.lesson || "";
  const home = document.body.dataset.page === "home";
  let state = null;

  // ---------- small utilities ----------
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // A tiny, safe markdown subset for tutor replies: code blocks, `code`, **bold**, "- " lists, paragraphs.
  function md(text) {
    const blocks = [];
    let src = esc(text).replace(/```(?:python|py)?\n?([\s\S]*?)```/g, (_, code) => {
      blocks.push(`<pre class="code">${code.replace(/\n$/, "")}</pre>`);
      return `\u0000${blocks.length - 1}\u0000`;
    });
    src = src.replace(/`([^`\n]+)`/g, "<code>$1</code>").replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    const isItem = (l) => /^\s*[-*] /.test(l);
    const out = src.split(/\n{2,}/).map((para) => {
      if (/^\u0000\d+\u0000$/.test(para.trim())) return para.trim();
      // Runs of "- " lines become a list; other lines become a paragraph.
      let html = "";
      let text = [];
      let items = [];
      const flushText = () => { if (text.length) { html += `<p>${text.join("<br>")}</p>`; text = []; } };
      const flushItems = () => { if (items.length) { html += "<ul>" + items.map((i) => `<li>${i}</li>`).join("") + "</ul>"; items = []; } };
      para.split("\n").forEach((l) => {
        if (isItem(l)) { flushText(); items.push(l.replace(/^\s*[-*] /, "")); }
        else { flushItems(); text.push(l); }
      });
      flushText();
      flushItems();
      return html;
    }).join("");
    return out.replace(/\u0000(\d+)\u0000/g, (_, i) => blocks[+i]);
  }

  async function api(path, body) {
    const res = await fetch("/api/" + path, body === undefined ? {} : {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "The course app didn't answer. Is it still running?");
    return data;
  }

  // Asks the app for a tutor reply and types it into `el` as it arrives.
  // The server sends one JSON line per piece of text. Gemini sends text in bursts,
  // so a typing loop reveals it at a steady pace, speeding up when it falls behind.
  // `onPaint` runs after each update (the chat uses it to keep scrolled to the bottom).
  async function streamReply(path, body, el, onPaint) {
    const res = await fetch("/api/" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok || !res.body) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "The course app didn't answer. Is it still running?");
    }
    const instant = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let target = "";
    let shown = 0;
    let finished = false;
    let error = null;

    const paint = (final) => {
      let text = target.slice(0, shown);
      // Close a half-arrived code block so it looks like code while it types.
      if (!final && (text.match(/```/g) || []).length % 2) text += "\n```";
      el.innerHTML = md(text);
      el.classList.toggle("streaming", !final);
      if (onPaint) onPaint();
    };

    // Browsers pause animation frames in hidden tabs, so fall back to a timer there.
    const later = (fn) => document.hidden ? setTimeout(() => fn(performance.now()), 100) : requestAnimationFrame(fn);
    const typing = new Promise((resolve) => {
      let last = performance.now();
      const tick = (now) => {
        const behind = target.length - shown;
        if (behind > 0) {
          // At least 60 characters a second; a long backlog drains in about 2 to 3 seconds.
          // Nobody is watching a hidden tab, so skip the typing there.
          const perSecond = instant || document.hidden ? Infinity : Math.max(60, behind * 1.5);
          shown = Math.min(target.length, shown + Math.max(1, Math.round(perSecond * (now - last) / 1000)));
          paint(false);
        }
        last = now;
        if (finished && shown >= target.length) {
          if (target) paint(true);
          return resolve();
        }
        later(tick);
      };
      later(tick);
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let cut;
        while ((cut = buffer.indexOf("\n")) >= 0) {
          const line = buffer.slice(0, cut).trim();
          buffer = buffer.slice(cut + 1);
          if (!line) continue;
          const msg = JSON.parse(line);
          if (msg.error) error = msg.error;
          else target += msg.text || "";
        }
      }
    } catch (_) {
      error = "The connection to the course app dropped part way through. Try again.";
    }
    finished = true;
    await typing;
    if (error) throw new Error(error);
    return target;
  }

  function post(type, detail) {
    const { element, ...rest } = detail;
    api("event", Object.assign({ type }, rest)).catch(() => {});
  }

  // ---------- Not on the app: offer a link if it's running ----------
  async function offerApp() {
    try {
      const res = await fetch(`http://localhost:${APP_PORT}/api/health`, { mode: "cors" });
      if (!res.ok) return;
      const rel = location.pathname.split("/").slice(-2).join("/");
      const target = home ? "" : (rel.startsWith("lessons/") ? rel.replace(/\.html$/, "") : "");
      const bar = document.createElement("div");
      bar.className = "app-banner";
      bar.innerHTML = `The course app is running. <a href="http://localhost:${APP_PORT}/${target}">Open this page in the app</a> to save progress and use the tutor.`;
      document.body.prepend(bar);
    } catch (_) { /* app not running: nothing to do */ }
  }

  // ---------- Account: sign in with Google, sign out, move progress ----------
  // Google's "G" mark, as its sign-in button guidelines require.
  const G_LOGO = '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>';

  function signInHref() {
    return "/auth/google?next=" + encodeURIComponent(location.pathname);
  }

  // ---------- Avatars: squishy characters to choose from ----------
  // Original drawings on a 100 x 100 grid: a soft shape, a two-colour gloss and a pair of eyes.
  const FLOWER = (() => {
    const pts = [];
    for (let i = 0; i < 64; i++) {
      const a = (i / 64) * Math.PI * 2, r = 36 + 6 * Math.cos(a * 8);
      pts.push(`${(50 + r * Math.sin(a)).toFixed(1)} ${(52 - r * Math.cos(a)).toFixed(1)}`);
    }
    return `<path d="M${pts.join("L")}Z"/>`;
  })();
  // A polygon with rounded corners (each corner becomes a curve r units long).
  const roundPoly = (pts, r) => {
    const toward = (p, q) => { const len = Math.hypot(q[0] - p[0], q[1] - p[1]); return [p[0] + (q[0] - p[0]) * r / len, p[1] + (q[1] - p[1]) * r / len].map((v) => v.toFixed(1)).join(" "); };
    return `<path d="${pts.map((p, i) => `${i ? "L" : "M"}${toward(p, pts[(i + pts.length - 1) % pts.length])}Q${p.join(" ")} ${toward(p, pts[(i + 1) % pts.length])}`).join("")}Z"/>`;
  };
  // [body, how far below the middle the eyes sit]
  const SHAPES = {
    round: ['<circle cx="50" cy="52" r="38"/>', 0],
    blob: ['<path d="M50 13c19 0 34 10 37 28 3 21-8 42-32 45-24 3-43-9-44-31-1-23 17-42 39-42z"/>', 0],
    squircle: ['<rect x="13" y="15" width="74" height="74" rx="28"/>', 0],
    pill: ['<rect x="7" y="28" width="86" height="48" rx="24"/>', 0],
    cat: ['<path d="M17 34 20 10 38 23Q50 19 62 23L80 10 83 34Q90 46 87 62 81 88 50 89 19 88 13 62 10 46 17 34Z"/>', 8],
    ghost: ['<path d="M15 88V50a35 35 0 0 1 70 0v38l-11.7-7-11.6 7-11.7-7-11.7 7-11.6-7z"/>', 2],
    flower: [FLOWER, 0],
    bot: ['<rect x="14" y="26" width="72" height="64" rx="24"/><rect x="47" y="10" width="6" height="18" rx="3"/><circle cx="50" cy="10" r="7"/>', 8],
    gem: [roundPoly([[50, 9], [91, 39], [76, 89], [24, 89], [9, 39]], 12), 8],
    drop: [roundPoly([[50, 6], [93, 87], [7, 87]], 16), 16],
  };
  const EYES = {
    pills: (y) => `<rect x="34" y="${y - 9}" width="9" height="18" rx="4.5"/><rect x="57" y="${y - 9}" width="9" height="18" rx="4.5"/>`,
    dashes: (y) => `<rect x="31" y="${y - 3}" width="14" height="6" rx="3"/><rect x="55" y="${y - 3}" width="14" height="6" rx="3"/>`,
    dots: (y) => `<circle cx="39" cy="${y}" r="7"/><circle cx="61" cy="${y}" r="7"/>`,
    stern: (y) => `<rect x="31" y="${y - 3}" width="14" height="6" rx="3" transform="rotate(14 38 ${y})"/><rect x="55" y="${y - 3}" width="14" height="6" rx="3" transform="rotate(-14 62 ${y})"/>`,
    happy: (y) => `<path d="M32 ${y + 3}q6-9 12 0M56 ${y + 3}q6-9 12 0" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`,
    sleepy: (y) => `<path d="M32 ${y}q6 6 12 0M56 ${y}q6 6 12 0" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>`,
  };
  // [name, shape, light colour, deep colour, eyes]
  const AVATARS = [
    ["mint-blob", "blob", "#c8f56a", "#2bb39a", "pills"],
    ["sky-round", "round", "#8fe3ff", "#2f8cf0", "dashes"],
    ["violet-flower", "flower", "#a38bff", "#5a32e8", "pills"],
    ["coral-cat", "cat", "#ff9a7a", "#e2334f", "dots"],
    ["ocean-ghost", "ghost", "#4fa3ff", "#13307a", "stern"],
    ["peach-squircle", "squircle", "#ffd3a6", "#ff6fa3", "happy"],
    ["amber-bot", "bot", "#ffd35c", "#c46a12", "pills"],
    ["lagoon-drop", "drop", "#7ff0e0", "#1592b8", "dashes"],
    ["plum-pill", "pill", "#ff8fd8", "#7b3cf0", "dots"],
    ["slate-cat", "cat", "#b7c8d6", "#5b7387", "stern"],
    ["rose-round", "round", "#ff9fb8", "#d81f5a", "sleepy"],
    ["night-gem", "gem", "#6f7dff", "#151a5c", "dashes"],
  ];
  let avatarCount = 0;
  function avatarSvg(name) {
    const a = AVATARS.find((x) => x[0] === name);
    if (!a) return "";
    const [, shape, light, deep, eyes] = a;
    const [body, dy] = SHAPES[shape];
    const id = `pfz-av-${++avatarCount}`;
    return `<svg class="avatar-art" viewBox="0 0 100 100" aria-hidden="true"><defs>` +
      `<linearGradient id="${id}f" x1="0.15" y1="0" x2="0.85" y2="1"><stop offset="0" stop-color="${light}"/><stop offset="1" stop-color="${deep}"/></linearGradient>` +
      `<radialGradient id="${id}g" cx="0.32" cy="0.26" r="0.55"><stop offset="0" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>` +
      `<g fill="url(#${id}f)">${body}</g><g fill="url(#${id}g)">${body}</g>` +
      `<g fill="#fff">${EYES[eyes](50 + dy)}</g></svg>`;
  }
  const avatarLabel = (name) => name.replace("-", " ").replace(/^./, (c) => c.toUpperCase());

  // What shows in the account button: a chosen avatar, else the Google photo, else the initial.
  function badgeHtml(user) {
    const initial = esc(user.name.trim().charAt(0).toUpperCase());
    const art = avatarSvg(user.avatar);
    if (art) return `<span class="avatar art" aria-hidden="true">${art}</span>`;
    const photo = user.picture && user.avatar !== "letter" ? `<img src="${esc(user.picture)}" alt="" referrerpolicy="no-referrer">` : "";
    return `<span class="avatar" aria-hidden="true">${initial}${photo}</span>`;
  }
  function watchPhotos(root) {
    root.querySelectorAll(".avatar img").forEach((img) => img.addEventListener("error", () => img.remove()));
  }

  function renderAccount() {
    const bar = document.querySelector(".topbar");
    if (!bar) return;
    // theme.js may have made the right-hand group already (for its theme button).
    let right = bar.querySelector(".topbar-right");
    if (!right) {
      right = document.createElement("div");
      right.className = "topbar-right";
      const where = bar.querySelector(".where");
      if (where) right.append(where);
      bar.append(right);
    }
    if (state.auth && !state.signedIn) {
      right.insertAdjacentHTML("beforeend", `<a class="gsi-btn" href="${esc(signInHref())}" aria-label="Sign in with Google">${G_LOGO}<span>Sign in<span class="gsi-long"> with Google</span></span></a>`);
      return;
    }
    const user = state.user;
    const label = user ? user.name.trim().split(/\s+/)[0] : "Progress";
    const badge = user
      ? badgeHtml(user)
      : '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 13.5h10M8 2.5v8M4.75 7.25 8 10.5l3.25-3.25" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    right.insertAdjacentHTML("beforeend", `
      <div class="account">
        <button type="button" class="account-btn" aria-haspopup="true" aria-expanded="false" aria-label="${esc(user ? `Account: ${user.name}` : "Progress")}">${badge}<span class="account-name">${esc(label)}</span></button>
        <div class="account-menu" hidden>
          <p class="who"><strong>${esc(user ? user.name : "Saved on this computer")}</strong><span>${esc(user ? user.email : "Download it to move your progress to another computer or to your account.")}</span></p>
          ${user ? `<button type="button" class="item pick-avatar" aria-expanded="false">Change avatar</button>
          <div class="avatar-picker" role="radiogroup" aria-label="Avatar" hidden>
            ${user.picture ? `<button type="button" class="avatar-opt" role="radio" data-avatar="google" aria-label="Google photo"><span class="avatar">${esc(user.name.trim().charAt(0).toUpperCase())}<img src="${esc(user.picture)}" alt="" referrerpolicy="no-referrer"></span></button>` : ""}
            <button type="button" class="avatar-opt" role="radio" data-avatar="letter" aria-label="Your initial"><span class="avatar">${esc(user.name.trim().charAt(0).toUpperCase())}</span></button>
            ${AVATARS.map((a) => `<button type="button" class="avatar-opt" role="radio" data-avatar="${a[0]}" aria-label="${avatarLabel(a[0])}">${avatarSvg(a[0])}</button>`).join("")}
          </div>` : ""}
          <a class="item" href="/api/progress/export" download>Download my progress</a>
          <button type="button" class="item upload">Upload a progress file</button>
          ${state.owner ? '<a class="item" href="/admin">Course overview</a>' : ""}
          ${state.auth ? '<button type="button" class="item signout">Sign out</button>' : ""}
          ${user ? '<button type="button" class="item danger delete-account">Delete my account</button>' : ""}
          <p class="legal small"><a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></p>
          <input type="file" accept=".json,application/json" hidden>
          <p class="menu-msg small" aria-live="polite"></p>
        </div>
      </div>`);
    const box = right.querySelector(".account");
    watchPhotos(box);
    const btn = box.querySelector(".account-btn");
    const menu = box.querySelector(".account-menu");
    const msg = box.querySelector(".menu-msg");
    const file = box.querySelector("input[type=file]");
    const open = (yes) => { menu.hidden = !yes; btn.setAttribute("aria-expanded", String(yes)); };
    btn.addEventListener("click", () => open(menu.hidden));
    document.addEventListener("click", (e) => { if (!box.contains(e.target)) open(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { open(false); btn.focus(); } });
    const picker = box.querySelector(".avatar-picker");
    if (picker) {
      const toggle = box.querySelector(".pick-avatar");
      const current = () => user.avatar || (user.picture ? "google" : "letter");
      const mark = () => picker.querySelectorAll(".avatar-opt").forEach((o) => o.setAttribute("aria-checked", String(o.dataset.avatar === current())));
      mark();
      toggle.addEventListener("click", () => {
        picker.hidden = !picker.hidden;
        toggle.setAttribute("aria-expanded", String(!picker.hidden));
      });
      picker.addEventListener("click", async (e) => {
        const opt = e.target.closest(".avatar-opt");
        if (!opt) return;
        try {
          await api("avatar", { avatar: opt.dataset.avatar });
          user.avatar = opt.dataset.avatar;
          btn.querySelector(".avatar").outerHTML = badgeHtml(user);
          watchPhotos(btn);
          mark();
        } catch (err) {
          msg.textContent = err.message;
        }
      });
    }
    box.querySelector(".upload").addEventListener("click", () => file.click());
    file.addEventListener("change", async () => {
      const chosen = file.files[0];
      file.value = "";
      if (!chosen) return;
      if (!confirm("Replace the progress saved here with the progress in this file?")) return;
      try {
        const res = await api("progress/import", JSON.parse(await chosen.text()));
        msg.textContent = `Loaded. ${res.completed.length} lesson${res.completed.length === 1 ? "" : "s"} done. Reloading...`;
        setTimeout(() => location.reload(), 900);
      } catch (e) {
        msg.textContent = e instanceof SyntaxError ? "That file isn't a progress file." : e.message;
      }
    });
    const del = box.querySelector(".delete-account");
    if (del) del.addEventListener("click", async () => {
      const typed = prompt("This deletes your account, progress, mistakes and tutor chats from the course. It can't be undone.\n\nYou can use \"Download my progress\" first to keep a copy.\n\nType delete to confirm.");
      if ((typed || "").trim().toLowerCase() !== "delete") return;
      try {
        await api("account/delete", { confirm: "delete" });
        location.href = "/";
      } catch (e) {
        msg.textContent = e.message;
      }
    });
    const out = box.querySelector(".signout");
    if (out) out.addEventListener("click", async () => {
      await fetch("/auth/logout", { method: "POST" }).catch(() => {});
      location.reload();
    });
  }

  // ---------- Home page ----------
  function renderHome() {
    const done = new Set(state.completed);
    document.querySelectorAll(".lesson-row").forEach((row) => {
      if (done.has(row.dataset.lesson)) row.classList.add("done");
    });
    const next = state.lessons.find((l) => !done.has(l.id));
    if (next) {
      const row = document.querySelector(`.lesson-row[data-lesson="${next.id}"]`);
      if (row) row.classList.add("next");
      const btn = document.querySelector(".continue-btn");
      if (btn) {
        btn.href = "lessons/" + next.url;
        btn.textContent = done.size ? `Continue with Lesson ${+next.id}` : "Start Lesson 1";
      }
    }
    const status = document.querySelector(".home-status");
    if (status) {
      const parts = [`${done.size} of ${state.lessons.length} lessons done`];
      if (state.dueCount) parts.push(`${state.dueCount} review question${state.dueCount === 1 ? "" : "s"} due`);
      parts.push(state.ai ? "AI tutor on" : "AI tutor off (add a Gemini key to .env)");
      if (!state.signedIn) parts.splice(0, parts.length, "Sign in with Google to save your progress and use the AI tutor");
      status.textContent = parts.join(" · ");
    }
  }

  // ---------- Review warm-up ----------
  function renderReview() {
    const slot = document.getElementById("review");
    if (!slot || !state.review || !state.review.length) return;
    const qs = state.review.map((q, i) => `
      <div class="quiz" data-qid="${esc(q.qid)}" data-review="1">
        <p class="q">${i + 1}. ${q.question} <span class="from">from Lesson ${+q.lesson}</span></p>
        <div class="options">${q.options.map((o) => `<button class="opt"${o.correct ? " data-correct" : ""}>${o.html}</button>`).join("")}</div>
        <p class="why">${q.why}</p>
      </div>`).join("");
    slot.innerHTML = `
      <div class="review card on-cloud">
        <h2>Quick review</h2>
        <p class="quiet">${state.review.length} question${state.review.length === 1 ? "" : "s"} from earlier lessons, picked for today. Ones you get wrong come back sooner.</p>
        ${qs}
      </div>`;
    slot.hidden = false;
    slot.querySelectorAll(".quiz").forEach((q) => window.PFZ.quiz.setup(q));
  }

  // ---------- Explain my mistake ----------
  function offerExplain(detail) {
    const ex = detail.element;
    if (!ex || detail.passed || detail.kind !== "check" && !detail.error) return;
    let btn = ex.querySelector(".explain-btn");
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-tool explain-btn";
      btn.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.75a4.25 4.25 0 0 0-2.5 7.7V11h5V9.45A4.25 4.25 0 0 0 8 1.75zM6 13.25h4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Explain my mistake</span>';
      ex.querySelector(".toolbar .status").before(btn);
      btn.addEventListener("click", async () => {
        const last = ex._lastDetail;
        let note = ex.querySelector(".tutor-note");
        if (!note) {
          note = document.createElement("div");
          note.className = "tutor-note";
          ex.querySelector(".window").append(note);
        }
        note.innerHTML = '<p class="label">Tutor</p><div class="reply"><p class="quiet thinking">Thinking</p></div>';
        const reply = note.querySelector(".reply");
        btn.disabled = true;
        try {
          const { element, ...payload } = last;
          await streamReply("explain", payload, reply);
        } catch (e) {
          // Keep any text that already arrived, then say what went wrong.
          if (reply.querySelector(".thinking")) reply.innerHTML = "";
          reply.classList.remove("streaming");
          reply.insertAdjacentHTML("beforeend", `<p class="err">${esc(e.message)}</p>`);
        }
        btn.disabled = false;
      });
    }
    ex._lastDetail = detail;
  }

  // ---------- Practice ----------
  function renderPractice() {
    const box = document.querySelector(".ai-practice");
    if (!box) return;
    if (state.ai && !state.signedIn) {
      box.innerHTML = `<p class="small quiet"><a href="${esc(signInHref())}">Sign in with Google</a> and your tutor will write practice exercises aimed at your weak spots.</p>`;
      return;
    }
    if (!state.ai) {
      box.innerHTML = '<p class="small quiet">The AI tutor is off. Add your Gemini API key to the <code>.env</code> file in the course folder, then restart the app.</p>';
      return;
    }
    box.innerHTML = `<button type="button" class="btn btn-primary make-practice">Write 3 practice exercises for me</button><p class="practice-msg small quiet" aria-live="polite"></p><div class="practice-list"></div>`;
    const btn = box.querySelector(".make-practice");
    const msg = box.querySelector(".practice-msg");
    const list = box.querySelector(".practice-list");
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      msg.textContent = "Writing exercises aimed at your weak spots. This takes up to a minute...";
      try {
        const { exercises } = await api("practice", { lesson });
        msg.textContent = "Checking each exercise with real Python before showing it...";
        let shown = 0;
        for (const ex of exercises) {
          const ok = await window.PFZ.runner.validate({ solution: ex.solution, starter: ex.starter, tests: ex.tests.join("\n"), inputs: ex.inputs });
          if (!ok) continue;
          shown++;
          list.append(practiceExercise(ex, list.children.length + 1));
        }
        msg.textContent = shown
          ? `${shown} exercise${shown === 1 ? "" : "s"} ready.${shown < exercises.length ? " (Some didn't pass the quality check and were left out.)" : ""} Want more? Press the button again.`
          : "None of the exercises passed the quality check this time. Press the button to try again.";
      } catch (e) {
        msg.textContent = e.message;
      }
      btn.disabled = false;
      btn.textContent = "Write 3 more";
    });
  }

  function practiceExercise(ex, n) {
    const id = `practice-${lesson}-${Date.now()}-${n}`;
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <div class="canvas exercise" id="${id}" data-file="${esc(ex.file)}" data-practice="1" data-no-save="1"${ex.inputs && ex.inputs.length ? ` data-inputs='${esc(JSON.stringify(ex.inputs))}'` : ""}>
        <div class="task"><h3>Practice ${n}: ${esc(ex.title)}</h3><p>${esc(ex.task)}</p></div>
        <textarea class="code" spellcheck="false">${esc(ex.starter)}</textarea>
        <script type="text/python" class="tests">${esc(ex.tests.join("\n"))}<\/script>
      </div>
      <details class="hint"><summary>A hint</summary><div><p>${esc(ex.hint)}</p></div></details>
      <details class="hint solution-reveal" hidden><summary>Show a solution</summary><div><pre class="code">${esc(ex.solution)}</pre></div></details>`;
    const exEl = wrap.querySelector(".exercise");
    // Script contents were escaped for safety; restore the real test text.
    exEl.querySelector("script.tests").textContent = ex.tests.join("\n");
    window.PFZ.runner.setup(exEl, id);
    const reveal = wrap.querySelector(".solution-reveal");
    document.addEventListener("pfz:exercise", (e) => {
      if (e.detail.id === id && (e.detail.passed || e.detail.attempts >= 3)) reveal.hidden = false;
    });
    return wrap;
  }

  // ---------- Finish button ----------
  function wireFinish() {
    const card = document.querySelector(".finish");
    if (!card) return;
    const btn = card.querySelector(".finish-btn");
    const msg = card.querySelector(".finish-msg");
    const markDone = (next) => {
      btn.textContent = `Lesson ${+lesson} done`;
      btn.disabled = true;
      msg.innerHTML = next ? `Saved. Next up: <a href="${esc(next.url)}">Lesson ${+next.id}: ${esc(next.nav_title)}</a>.` : "Saved.";
    };
    if (state && state.completed.includes(lesson)) {
      const next = state.lessons.find((l) => l.id > lesson && !state.completed.includes(l.id));
      markDone(next);
    }
    btn.addEventListener("click", async () => {
      if (!state) {
        msg.textContent = "Progress is saved by the course app. Start it with the Python from zero shortcut, then press this again.";
        return;
      }
      if (!state.signedIn) {
        msg.innerHTML = `<a href="${esc(signInHref())}">Sign in with Google</a> to save your progress.`;
        return;
      }
      try {
        const res = await api("complete", { lesson });
        markDone(res.next);
      } catch (e) {
        msg.textContent = e.message;
      }
    });
  }

  // ---------- Feedback on a lesson ----------
  function renderFeedback() {
    const finish = document.querySelector(".finish");
    if (!finish || !state.signedIn) return;
    const box = document.createElement("details");
    box.className = "hint feedback";
    box.innerHTML = `<summary>Something unclear or wrong in this lesson? Tell us</summary>
      <div><form class="feedback-form">
        <label for="feedback-text" class="small quiet">Which part, and what was confusing or broken? Your note goes to the person who runs the course.</label>
        <textarea id="feedback-text" rows="3" maxlength="2000"></textarea>
        <div class="feedback-row"><button type="submit" class="btn btn-primary">Send</button><span class="small quiet feedback-msg" aria-live="polite"></span></div>
      </form></div>`;
    finish.after(box);
    const form = box.querySelector("form");
    const text = form.querySelector("textarea");
    const note = form.querySelector(".feedback-msg");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!text.value.trim()) { note.textContent = "Write a note first."; return; }
      try {
        await api("feedback", { lesson, page: location.pathname, message: text.value });
        text.value = "";
        note.textContent = "Sent. Thank you.";
      } catch (err) {
        note.textContent = err.message;
      }
    });
  }

  // ---------- Chat ----------
  function renderChat() {
    if (!state.ai) return;
    if (!state.signedIn) {
      const link = document.createElement("a");
      link.className = "chat-launcher btn btn-primary";
      link.href = signInHref();
      link.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.75 3.5h10.5v7h-6l-3 2.5v-2.5h-1.5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg><span>Sign in to ask your tutor</span>';
      document.body.append(link);
      return;
    }
    const launcher = document.createElement("button");
    launcher.type = "button";
    launcher.className = "chat-launcher btn btn-primary";
    launcher.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.75 3.5h10.5v7h-6l-3 2.5v-2.5h-1.5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg><span>Ask your tutor</span>';
    const panel = document.createElement("aside");
    panel.className = "chat-panel";
    panel.hidden = true;
    panel.setAttribute("aria-label", "Tutor chat");
    panel.innerHTML = `
      <div class="chat-head"><strong>Your tutor</strong><span class="quiet small">knows this lesson and your mistakes</span><button type="button" class="chat-close" aria-label="Close chat"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></button></div>
      <div class="chat-log" aria-live="polite"></div>
      <form class="chat-form"><textarea rows="2" placeholder="Ask anything about this lesson" aria-label="Your question"></textarea><button type="submit" class="btn btn-primary">Send</button></form>`;
    document.body.append(launcher, panel);
    const log = panel.querySelector(".chat-log");
    const form = panel.querySelector("form");
    const input = form.querySelector("textarea");
    const add = (role, text) => {
      const div = document.createElement("div");
      div.className = "msg " + role;
      div.innerHTML = role === "user" ? `<p>${esc(text).replace(/\n/g, "<br>")}</p>` : md(text);
      log.append(div);
      log.scrollTop = log.scrollHeight;
      return div;
    };
    (state.chat || []).forEach((m) => add(m.role, m.text));
    if (!state.chat || !state.chat.length) add("tutor", "Ask me anything about this lesson: a word you didn't get, an error message, or why something works the way it does. Paste code if you like.");
    launcher.addEventListener("click", () => { panel.hidden = false; launcher.hidden = true; input.focus(); });
    panel.querySelector(".chat-close").addEventListener("click", () => { panel.hidden = true; launcher.hidden = false; launcher.focus(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
    });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      add("user", text);
      const bubble = add("tutor waiting", "");
      bubble.innerHTML = '<p class="thinking">Thinking</p>';
      // Follow the reply down as it types, unless the learner has scrolled up to read.
      let follow = true;
      const onScroll = () => { follow = log.scrollHeight - log.scrollTop - log.clientHeight < 40; };
      log.addEventListener("scroll", onScroll);
      const paint = () => {
        bubble.classList.remove("waiting");
        if (follow) log.scrollTop = log.scrollHeight;
      };
      try {
        await streamReply("chat", { lesson, message: text }, bubble, paint);
      } catch (err) {
        if (bubble.querySelector(".thinking")) bubble.remove();
        else bubble.classList.remove("streaming");
        add("tutor error", err.message);
      }
      log.removeEventListener("scroll", onScroll);
    });
    window.PFZ.openChat = (text) => { launcher.click(); if (text) input.value = text; };
  }

  // ---------- Events from the lesson ----------
  const saving = () => state && state.signedIn;
  document.addEventListener("pfz:exercise", (e) => {
    if (!saving()) return;
    post("exercise", e.detail);
    if (state.ai) offerExplain(e.detail);
  });
  document.addEventListener("pfz:quiz", (e) => { if (saving()) post("quiz", e.detail); });
  document.addEventListener("pfz:paste", (e) => { if (saving()) post("paste", e.detail); });

  // ---------- Start ----------
  async function init() {
    window.PFZ = window.PFZ || {};
    if (!onApp) {
      wireFinish();
      offerApp();
      return;
    }
    try {
      state = await api("state" + (lesson ? `?lesson=${encodeURIComponent(lesson)}` : ""));
    } catch (_) {
      wireFinish();
      return;
    }
    document.body.classList.add("on-app");
    renderAccount();
    if (home) return renderHome();
    renderReview();
    renderPractice();
    wireFinish();
    renderFeedback();
    renderChat();
  }
  init();
})();
