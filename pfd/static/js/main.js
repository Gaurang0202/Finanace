// main.js -- small cross-page UX helpers (sidebar toggle, delete confirmations, auto-dismiss alerts)

document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Auto-dismiss flash alerts after 5s
  document.querySelectorAll(".flash-stack .alert").forEach((el) => {
    setTimeout(() => {
      if (window.bootstrap) {
        const alert = window.bootstrap.Alert.getOrCreateInstance(el);
        alert.close();
      }
    }, 5000);
  });

  // SweetAlert2-powered delete confirmations for any form with data-confirm-delete
  document.querySelectorAll("form[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (form.dataset.confirmed === "true") return;
      e.preventDefault();
      const label = form.dataset.confirmDelete || "this item";
      if (window.Swal) {
        Swal.fire({
          title: "Are you sure?",
          text: `This will permanently delete ${label}.`,
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#e6553f",
          cancelButtonColor: "#6c5ce7",
          confirmButtonText: "Yes, delete it",
        }).then((result) => {
          if (result.isConfirmed) {
            form.dataset.confirmed = "true";
            form.requestSubmit(); // (not .submit() -- that bypasses the 'submit' event and our loading-button state)
          }
        });
      } else if (confirm(`Delete ${label}?`)) {
        form.dataset.confirmed = "true";
        form.requestSubmit();
      }
    });
  });

  // --- Floating nav: transparent at the top, glass once scrolled ---------
  const siteNav = document.getElementById("siteNav");
  if (siteNav) {
    const onScroll = () => siteNav.classList.toggle("scrolled", window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // --- Scroll-reveal for landing/story sections ---------------------------
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      revealEls.forEach((el) => el.classList.add("in-view"));
    } else {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("in-view");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15 }
      );
      revealEls.forEach((el) => observer.observe(el));
    }
  }

  // --- Lightweight page-leave fade for internal navigation ----------------
  // This is a traditional multi-page Flask app, so we fake a "transition"
  // with a quick fade-out before the browser navigates, rather than a real
  // client-side router. Skipped entirely under reduced-motion.
  if (!reduceMotion) {
    document.querySelectorAll('a[href]:not([target="_blank"]):not([href^="#"]):not([href^="mailto:"])').forEach((link) => {
      link.addEventListener("click", (e) => {
        const url = new URL(link.href, window.location.origin);
        if (url.origin !== window.location.origin) return; // external links navigate normally
        if (e.metaKey || e.ctrlKey || e.shiftKey) return;   // let modified clicks (new tab) through
        e.preventDefault();
        document.body.classList.add("page-leaving");
        setTimeout(() => { window.location.href = link.href; }, 180);
      });
    });
  }

  // --- Authentication button loading states (login / register) ------------
  // Real form submits (this is a server-rendered app), but we still give
  // immediate feedback and guard against double-submits while the browser
  // waits for the redirect, plus the same fade used for link navigation.
  document.querySelectorAll("form[data-loading-label]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector('button[type="submit"]');
      if (!btn || btn.classList.contains("btn-loading")) return; // already submitting
      btn.textContent = form.dataset.loadingLabel;
      btn.classList.add("btn-loading");
      btn.setAttribute("aria-busy", "true");
      if (!reduceMotion) document.body.classList.add("page-leaving");
    });
  });

  // Icon-only delete buttons: same spinner treatment, but never swap in text
  // (there's no room for a label inside a small circular icon button).
  document.querySelectorAll("form[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", () => {
      if (form.dataset.confirmed !== "true") return; // still the intercepted first click -- dialog not confirmed yet
      const btn = form.querySelector('button[type="submit"]');
      if (!btn || btn.classList.contains("btn-loading")) return;
      btn.classList.add("btn-loading");
      btn.setAttribute("aria-busy", "true");
    });
  });

  // --- Animated number counters (used on the dashboard hero metric) -------
  document.querySelectorAll("[data-count-to]").forEach((el) => {
    const target = parseFloat(el.dataset.countTo);
    if (Number.isNaN(target)) return;
    const prefix = el.dataset.countPrefix || "";
    const duration = reduceMotion ? 0 : 900;
    const start = performance.now();
    function tick(now) {
      const progress = duration === 0 ? 1 : Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(target * eased);
      el.textContent = prefix + value.toLocaleString("en-IN");
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});
