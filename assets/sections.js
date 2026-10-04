/*
  Pill segmented switcher that jumps between a page's parts and tracks the one in view.

  Markup:
    <div class="switcher-wrap">
      <nav class="switcher" aria-label="Lesson sections">
        <a href="#print">Print</a>
        <a href="#numbers">Numbers</a>
      </nav>
    </div>
    ...
    <section class="part" id="print">...</section>

  The active link gets aria-current="true"; a sliding thumb sits behind it.
*/
(function () {
  const nav = document.querySelector(".switcher");
  if (!nav) return;
  const links = Array.from(nav.querySelectorAll("a[href^='#']"));
  const targets = links.map((a) => document.getElementById(a.getAttribute("href").slice(1)));
  const thumb = document.createElement("span");
  thumb.className = "thumb";
  thumb.setAttribute("aria-hidden", "true");
  nav.prepend(thumb);

  let current = -1;
  function setActive(i) {
    if (i === current) return;
    current = i;
    links.forEach((a, j) => (j === i ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current")));
    if (i < 0) { thumb.style.width = "0px"; return; }
    const a = links[i];
    thumb.style.width = a.offsetWidth + "px";
    thumb.style.transform = `translateX(${a.offsetLeft}px)`;
    // When the row is wider than the screen, slide it so the current part stays in view.
    if (nav.scrollWidth > nav.clientWidth) {
      const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
      nav.scrollTo({ left: a.offsetLeft - (nav.clientWidth - a.offsetWidth) / 2, behavior: smooth ? "smooth" : "auto" });
    }
  }

  function update() {
    const line = window.innerHeight * 0.35;
    let active = -1;
    targets.forEach((t, i) => { if (t && t.getBoundingClientRect().top <= line) active = i; });
    // Before the first part, highlight the first segment so the control never looks empty.
    setActive(active < 0 ? 0 : active);
  }

  let ticking = false;
  window.addEventListener("scroll", () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { update(); ticking = false; });
  }, { passive: true });
  window.addEventListener("resize", () => { const i = current; current = -1; setActive(i); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { const i = current; current = -1; setActive(i); });
  update();
})();
