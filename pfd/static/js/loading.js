// loading.js -- perceived-performance helpers shared across pages:
//   1. WealthrLoading.withTimedLoading(...) -- wraps a fetch/render cycle with
//      the timing tiers from the brief (no flash under ~250ms, skeleton after
//      that, contextual message at 2s, "taking longer than usual" at 5s).
//   2. A global offline/reconnect banner, since a slow/dropped connection can
//      happen on any page, not just ones with charts.

(function () {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------------
  // Timed loading wrapper
  // ---------------------------------------------------------------------
  function withTimedLoading(overlayEl, noteEl, fetchFn, renderFn, opts) {
    opts = opts || {};
    const revealDelay = opts.revealDelay ?? 250;     // don't show skeleton for fast responses
    const slowNoteAt = opts.slowNoteAt ?? 2000;       // "Loading your latest activity..."
    const verySlowNoteAt = opts.verySlowNoteAt ?? 5000; // "taking a little longer than usual"
    const slowText = opts.slowText || "Loading the latest data\u2026";
    const verySlowText = opts.verySlowText || "This is taking a little longer than usual.";

    let settled = false;
    const timers = [];

    if (overlayEl) overlayEl.setAttribute("aria-busy", "true");

    if (!reduceMotion) {
      timers.push(setTimeout(() => { if (!settled && overlayEl) overlayEl.classList.remove("hidden"); }, revealDelay));
    } else if (overlayEl) {
      overlayEl.classList.remove("hidden"); // no flicker-avoidance dance under reduced motion; just show it
    }

    timers.push(setTimeout(() => {
      if (!settled && noteEl) { noteEl.textContent = slowText; noteEl.classList.add("visible"); }
    }, slowNoteAt));

    timers.push(setTimeout(() => {
      if (!settled && noteEl) { noteEl.textContent = verySlowText; noteEl.classList.add("visible"); }
    }, verySlowNoteAt));

    function finish() {
      settled = true;
      timers.forEach(clearTimeout);
      if (overlayEl) { overlayEl.classList.add("hidden"); overlayEl.removeAttribute("aria-busy"); }
      if (noteEl) { noteEl.classList.remove("visible"); }
    }

    return fetchFn()
      .then((data) => { finish(); renderFn(data); })
      .catch((err) => {
        finish();
        if (noteEl) {
          noteEl.textContent = "Couldn't load this right now.";
          noteEl.classList.add("visible");
        }
        console.error("withTimedLoading error:", err);
      });
  }

  window.WealthrLoading = { withTimedLoading };

  // ---------------------------------------------------------------------
  // Global offline / reconnect banner
  // ---------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    const banner = document.getElementById("networkBanner");
    const textEl = document.getElementById("networkBannerText");
    const retryBtn = document.getElementById("networkRetryBtn");
    if (!banner || !textEl) return;

    let hideTimer = null;

    function showOffline() {
      clearTimeout(hideTimer);
      banner.classList.remove("restored");
      banner.classList.add("offline", "visible");
      textEl.textContent = "You're offline. We're having trouble connecting.";
      retryBtn.style.display = "";
    }

    function showRestored() {
      banner.classList.remove("offline");
      banner.classList.add("restored", "visible");
      textEl.textContent = "Connection restored.";
      retryBtn.style.display = "none";
      hideTimer = setTimeout(() => banner.classList.remove("visible"), 2500);
    }

    window.addEventListener("offline", showOffline);
    window.addEventListener("online", showRestored);
    if (!navigator.onLine) showOffline();

    retryBtn?.addEventListener("click", () => {
      if (navigator.onLine) {
        window.location.reload();
      } else {
        // Still offline -- give a small shake-style acknowledgement rather than pretending it worked.
        banner.animate(
          [{ transform: "translateX(-50%) translateY(0)" }, { transform: "translateX(calc(-50% - 4px)) translateY(0)" }, { transform: "translateX(-50%) translateY(0)" }],
          { duration: 200 }
        );
      }
    });
  });
})();
