// onboarding.js -- cinematic interactive product tour.
// Targets real interface elements via [data-tour="..."] attributes already
// present in base.html / dashboard.html. Completion is persisted server-side
// (routes/onboarding.py) so it follows the account, not just this browser.

(function () {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const steps = [
    { selector: '[data-tour="nav-sidebar"]', title: "Your command center.", text: "Everything you need is available from here — income, expenses, budgets, goals and more." },
    { selector: '[data-tour="dashboard-overview"]', title: "Your overview.", text: "Everything important is summarized here so you can understand what's happening at a glance." },
    { selector: '[data-tour="primary-action"]', title: "Start here.", text: "This is where you'll log a new expense — the action you'll use most." },
    { selector: '[data-tour="notifications"]', title: "Stay informed.", text: "Budget warnings, large expenses and goal milestones will show up here." },
    { selector: '[data-tour="profile"]', title: "Make it yours.", text: "Manage your account, switch themes, and customize your experience here." },
  ];

  let stepIndex = 0;

  const welcome = document.getElementById("tourWelcome");
  const final = document.getElementById("tourFinal");
  const scrim = document.getElementById("tourScrim");
  const spotlight = document.getElementById("tourSpotlight");
  const tooltip = document.getElementById("tourTooltip");
  const progressWrap = document.getElementById("tourProgress");
  const titleEl = document.getElementById("tourTitle");
  const textEl = document.getElementById("tourText");
  const stepCountEl = document.getElementById("tourStepCount");
  const csrfToken = document.getElementById("onboardingCsrf")?.value;

  if (!welcome || !scrim) return; // partial not present on this page

  // Build progress dots once.
  steps.forEach(() => {
    const dot = document.createElement("span");
    progressWrap.appendChild(dot);
  });

  function markComplete() {
    fetch("/onboarding/complete", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `csrf_token=${encodeURIComponent(csrfToken || "")}`,
    }).catch(() => {}); // non-fatal if this fails -- tour just won't be remembered
  }

  function positionOn(el) {
    const rect = el.getBoundingClientRect();
    const pad = 8;
    spotlight.style.top = `${rect.top - pad}px`;
    spotlight.style.left = `${rect.left - pad}px`;
    spotlight.style.width = `${rect.width + pad * 2}px`;
    spotlight.style.height = `${rect.height + pad * 2}px`;

    // Position tooltip near the element, flipping side to stay on-screen.
    const tooltipWidth = 300;
    let top = rect.bottom + 16;
    let left = rect.left;

    if (left + tooltipWidth > window.innerWidth - 16) {
      left = window.innerWidth - tooltipWidth - 16;
    }
    if (top + 180 > window.innerHeight) {
      top = Math.max(16, rect.top - 190);
    }
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${Math.max(16, left)}px`;
  }

  function renderStep() {
    const step = steps[stepIndex];
    const el = document.querySelector(step.selector);

    if (!el) {
      // Target isn't on this page/viewport (e.g. sidebar hidden on mobile) -- skip it.
      stepIndex += 1;
      if (stepIndex >= steps.length) return finishTour();
      return renderStep();
    }

    // On small screens the sidebar is off-canvas; open it for that step.
    if (step.selector.includes("nav-sidebar")) {
      document.getElementById("sidebar")?.classList.add("open");
    } else {
      document.getElementById("sidebar")?.classList.remove("open");
    }

    titleEl.textContent = step.title;
    textEl.textContent = step.text;
    stepCountEl.textContent = `Step ${stepIndex + 1} of ${steps.length}`;
    [...progressWrap.children].forEach((dot, i) => dot.classList.toggle("done", i <= stepIndex));

    // Give layout a tick to settle (e.g. sidebar opening) before measuring.
    requestAnimationFrame(() => {
      positionOn(el);
      tooltip.classList.add("active");
    });

    el.scrollIntoView({ block: "center", behavior: reduceMotion ? "auto" : "smooth" });
  }

  function startTour() {
    welcome.classList.remove("active");
    scrim.classList.add("active");
    stepIndex = 0;
    renderStep();
  }

  function nextStep() {
    tooltip.classList.remove("active");
    stepIndex += 1;
    if (stepIndex >= steps.length) {
      finishTour();
    } else {
      setTimeout(renderStep, reduceMotion ? 0 : 150);
    }
  }

  function finishTour() {
    scrim.classList.remove("active");
    tooltip.classList.remove("active");
    document.getElementById("sidebar")?.classList.remove("open");
    final.classList.add("active");
    markComplete();
  }

  function skipTour() {
    welcome.classList.remove("active");
    scrim.classList.remove("active");
    tooltip.classList.remove("active");
    document.getElementById("sidebar")?.classList.remove("open");
    markComplete();
  }

  document.getElementById("tourStartBtn")?.addEventListener("click", startTour);
  document.getElementById("tourSkipBtn")?.addEventListener("click", skipTour);
  document.getElementById("tourSkipBtn2")?.addEventListener("click", skipTour);
  document.getElementById("tourNextBtn")?.addEventListener("click", nextStep);
  document.getElementById("tourEnterBtn")?.addEventListener("click", () => final.classList.remove("active"));

  window.addEventListener("resize", () => {
    if (scrim.classList.contains("active")) {
      const step = steps[stepIndex];
      const el = step && document.querySelector(step.selector);
      if (el) positionOn(el);
    }
  });

  // Reveal the welcome card shortly after paint for a premium, non-jarring entrance.
  requestAnimationFrame(() => setTimeout(() => welcome.classList.add("active"), reduceMotion ? 0 : 400));
})();
