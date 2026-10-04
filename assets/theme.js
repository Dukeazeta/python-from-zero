/*
  Light or dim (deep navy) colours. "Auto" follows the device's setting; the round button in
  the top bar cycles Auto, Light and Dim, and remembers the choice in this browser.
  Loaded in <head> so the right colours apply before the page first draws.
*/
(function () {
  const KEY = "pfz-theme";
  const root = document.documentElement;
  const ORDER = ["auto", "light", "dark"];
  const LABEL = { auto: "Theme: automatic", light: "Theme: light", dark: "Theme: dim" };
  const ICON = {
    auto: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 3.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg>',
    light: '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    dark: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M15.5 12.6A6.5 6.5 0 0 1 7.4 4.5a6.5 6.5 0 1 0 8.1 8.1z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
  };

  let choice = "auto";
  try { choice = localStorage.getItem(KEY) || "auto"; } catch (_) { /* storage blocked: follow the device */ }
  if (!ORDER.includes(choice)) choice = "auto";
  const apply = () => { if (choice === "auto") delete root.dataset.theme; else root.dataset.theme = choice; };
  apply();

  document.addEventListener("DOMContentLoaded", () => {
    const bar = document.querySelector(".topbar");
    if (!bar) return;
    let right = bar.querySelector(".topbar-right");
    if (!right) {
      right = document.createElement("div");
      right.className = "topbar-right";
      const where = bar.querySelector(".where");
      if (where) right.append(where);
      bar.append(right);
    }
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "theme-btn";
    const show = () => { btn.innerHTML = ICON[choice]; btn.setAttribute("aria-label", LABEL[choice]); btn.title = LABEL[choice]; };
    show();
    btn.addEventListener("click", () => {
      choice = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length];
      try { localStorage.setItem(KEY, choice); } catch (_) { /* fine: lasts until the page closes */ }
      apply();
      show();
    });
    right.append(btn);
  });
})();
