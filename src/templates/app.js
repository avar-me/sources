// sources.avar.me — minimal client-side behavior.
// Static letter pages don't need JS to read, but a few niceties help.

(function () {
  // Auto-collapse TOC after navigation on small screens to keep entries visible.
  function autoCloseTocOnNav() {
    var toc = document.querySelector(".toc");
    if (!toc) return;
    document.querySelectorAll(".toc-list a").forEach(function (a) {
      a.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 38rem)").matches) {
          toc.removeAttribute("open");
        }
      });
    });
  }

  // Highlight the entry referenced by the URL hash on load.
  function flashHash() {
    if (!location.hash) return;
    var el = document.querySelector(location.hash);
    if (!el) return;
    // Smooth-scroll past the sticky header.
    setTimeout(function () {
      el.scrollIntoView({ block: "start", behavior: "smooth" });
    }, 30);
  }

  document.addEventListener("DOMContentLoaded", function () {
    autoCloseTocOnNav();
    flashHash();
  });
})();
