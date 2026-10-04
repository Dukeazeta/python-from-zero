/*
  Multiple-choice retrieval quiz.

  Markup:
    <div class="quiz" data-qid="0003-q1">
      <p class="q">Question?</p>
      <div class="options">
        <button class="opt" data-correct>Right answer</button>
        <button class="opt">Wrong answer</button>
      </div>
      <p class="why">Shown after the right answer is picked.</p>
    </div>

  Options are shuffled on load so position never hints at the answer.
  Wrong picks are disabled and the learner keeps trying until correct.
  Fires "pfz:quiz" on document when the right answer is found, with
  { qid, lesson, firstTry, wrongPicks }. window.PFZ.quiz.setup(el) wires up
  quizzes added later (the adaptive warm-up).
*/
(function () {
  const CHECK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function shuffle(parent) {
    const kids = Array.from(parent.children);
    for (let i = kids.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [kids[i], kids[j]] = [kids[j], kids[i]];
    }
    kids.forEach((k) => parent.appendChild(k));
  }

  function setup(quiz) {
    if (quiz.dataset.ready) return;
    quiz.dataset.ready = "1";
    const options = quiz.querySelector(".options");
    const why = quiz.querySelector(".why");
    const feedback = document.createElement("p");
    feedback.className = "feedback";
    feedback.setAttribute("aria-live", "polite");
    (why || options).after(feedback);
    shuffle(options);

    let tries = 0;
    const wrongPicks = [];
    options.querySelectorAll("button.opt").forEach((btn) => {
      btn.type = "button";
      btn.insertAdjacentHTML("beforeend", CHECK);
      btn.addEventListener("click", () => {
        tries++;
        if (btn.hasAttribute("data-correct")) {
          btn.classList.add("right");
          options.querySelectorAll("button.opt").forEach((b) => (b.disabled = true));
          feedback.className = "feedback right";
          const lead = tries === 1 ? "Correct, first try." : "Correct.";
          feedback.textContent = lead + (why ? " " + why.textContent.trim() : "");
          document.dispatchEvent(new CustomEvent("pfz:quiz", {
            detail: {
              qid: quiz.dataset.qid || "",
              lesson: document.body.dataset.lesson || "",
              firstTry: tries === 1,
              wrongPicks,
              question: (quiz.querySelector(".q") || {}).innerText || "",
              review: Boolean(quiz.dataset.review),
            },
          }));
        } else {
          btn.classList.add("wrong");
          btn.disabled = true;
          wrongPicks.push(btn.innerText.trim());
          feedback.className = "feedback wrong";
          feedback.textContent = "Not that one. Think it through and pick again.";
        }
      });
    });
  }

  window.PFZ = window.PFZ || {};
  window.PFZ.quiz = { setup };
  document.querySelectorAll(".quiz").forEach(setup);
})();
