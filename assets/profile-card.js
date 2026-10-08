/*
  A preview of the course author's X profile, shown when the X icon in the footer is hovered
  (with a mouse) or focused with the keyboard. One card that fades up, unblurs and settles,
  like the page previews in Ochà Prime's navigation. On touch screens, a tap just opens X.

  The profile pictures are only fetched from X the first time the card opens, so visitors who
  never hover the icon don't contact X at all.
*/
(function () {
  const PROFILE = {
    url: "https://x.com/_dukedev",
    name: "DUKE",
    handle: "@_dukedev",
    bio: "swe | mobile & web",
    site: "dukedev.space",
    avatar: "https://pbs.twimg.com/profile_images/2027987067729534976/kHU54zMc_400x400.jpg",
    banner: "https://pbs.twimg.com/profile_banners/1516124958317023234/1762635321/1500x500",
  };
  const ARROW = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  document.addEventListener("DOMContentLoaded", () => {
    const link = document.querySelector(".x-link");
    if (!link) return;
    const wrap = link.parentElement;
    const card = document.createElement("div");
    card.className = "profile-card";
    card.setAttribute("aria-hidden", "true");
    card.hidden = true;  // takes no space until it opens, so phones never scroll sideways
    card.innerHTML = `
      <a class="profile-card-inner" href="${PROFILE.url}" target="_blank" rel="noopener" tabindex="-1">
        <span class="profile-banner"><img alt="" referrerpolicy="no-referrer" data-src="${PROFILE.banner}"></span>
        <span class="profile-avatar">D<img alt="" referrerpolicy="no-referrer" data-src="${PROFILE.avatar}"></span>
        <span class="profile-body">
          <span class="profile-name">${PROFILE.name}</span>
          <span class="profile-handle">${PROFILE.handle}</span>
          <span class="profile-bio">${PROFILE.bio}</span>
          <span class="profile-foot"><span>${PROFILE.site}</span><span class="profile-cta">View on X ${ARROW}</span></span>
        </span>
      </a>`;
    wrap.append(card);
    card.querySelectorAll("img").forEach((img) => img.addEventListener("error", () => img.remove()));

    let closeTimer = null;
    const cancelClose = () => { clearTimeout(closeTimer); closeTimer = null; };
    const open = () => {
      cancelClose();
      card.querySelectorAll("img[data-src]").forEach((img) => { img.src = img.dataset.src; img.removeAttribute("data-src"); });
      // Keep the card on screen: centre it on the icon, but not past either edge.
      const r = link.getBoundingClientRect();
      const width = card.offsetWidth || 300;
      const left = Math.min(Math.max(r.left + r.width / 2 - width / 2, 12), window.innerWidth - width - 12);
      card.style.left = `${left - wrap.getBoundingClientRect().left}px`;
      card.hidden = false;
      void card.offsetWidth;  // let the browser lay it out before animating in
      card.classList.add("open");
    };
    const close = () => { cancelClose(); card.classList.remove("open"); setTimeout(() => { if (!card.classList.contains("open")) card.hidden = true; }, 450); };
    const scheduleClose = () => { cancelClose(); closeTimer = setTimeout(close, 140); };

    link.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") open(); });
    link.addEventListener("pointerleave", scheduleClose);
    link.addEventListener("focus", () => { if (link.matches(":focus-visible")) open(); });
    link.addEventListener("blur", scheduleClose);
    card.addEventListener("pointerenter", cancelClose);
    card.addEventListener("pointerleave", scheduleClose);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  });
})();
