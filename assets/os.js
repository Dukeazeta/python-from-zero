/*
  Shows commands and steps for the learner's own computer: Windows, Mac or Linux.

  Anything marked data-os="windows", data-os="mac", data-os="linux" (or several, like
  data-os="mac linux") only shows when it matches. The choice is guessed from the browser,
  and every <div class="os-switch"></div> becomes a Windows / Mac / Linux switch that changes
  it on every page. Loaded in <head> so the right version shows from the first paint.
*/
(function () {
  const KEY = "pfz-os";
  const NAMES = [["windows", "Windows"], ["mac", "Mac"], ["linux", "Linux"]];

  function guess() {
    const ua = navigator.userAgent.toLowerCase();
    const platform = ((navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "").toLowerCase();
    // Phones can't run the terminal steps; most people then use a Windows computer for them.
    if (ua.includes("android")) return "windows";
    if (platform.includes("mac") || /iphone|ipad/.test(ua)) return "mac";
    if (platform.includes("linux") || platform.includes("x11") || ua.includes("cros")) return "linux";
    return "windows";
  }

  let saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) { /* storage blocked: use the guess */ }
  const root = document.documentElement;
  root.dataset.os = NAMES.some(([v]) => v === saved) ? saved : guess();

  function choose(os) {
    root.dataset.os = os;
    try { localStorage.setItem(KEY, os); } catch (_) { /* fine: it lasts until the page closes */ }
    document.querySelectorAll(".os-switch button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pick === os)));
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".os-switch").forEach((box) => {
      box.setAttribute("role", "group");
      box.setAttribute("aria-label", "Your computer");
      box.innerHTML = '<span class="os-label">Your computer:</span>' + NAMES.map(([v, label]) =>
        `<button type="button" data-pick="${v}" aria-pressed="${v === root.dataset.os}">${label}</button>`).join("");
      box.addEventListener("click", (e) => {
        const b = e.target.closest("button[data-pick]");
        if (b) choose(b.dataset.pick);
      });
    });
  });
})();
