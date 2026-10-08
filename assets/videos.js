/*
  Section videos: a thumbnail card that turns into a YouTube player inside the page.

  Markup (written by tools/build.py from content/videos.json):
    <div class="video" data-yt="VIDEO_ID">
      <button class="video-play">thumbnail, play icon, length</button>
      <div class="video-meta">title, channel, link</div>
    </div>

  Nothing loads from YouTube until a video is played, apart from the thumbnail. The player uses
  youtube-nocookie.com, which doesn't set cookies until you play. Starting one video closes any
  other that is playing, so two never talk at once.
*/
(function () {
  let open = null;

  function close(card) {
    const frame = card.querySelector(".video-frame");
    if (frame) frame.remove();
    card.classList.remove("playing");
    card.querySelector(".video-play").hidden = false;
  }

  function play(card) {
    if (open && open !== card) close(open);
    open = card;
    const id = card.dataset.yt;
    const title = card.querySelector(".video-title").textContent;
    const wrap = document.createElement("div");
    wrap.className = "video-frame";
    const iframe = document.createElement("iframe");
    iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&playsinline=1`;
    iframe.title = title;
    iframe.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    wrap.append(iframe);
    const button = card.querySelector(".video-play");
    button.hidden = true;
    card.prepend(wrap);
    card.classList.add("playing");
    iframe.focus();
  }

  document.addEventListener("click", (e) => {
    const button = e.target.closest(".video-play");
    if (button) play(button.closest(".video"));
  });
})();
