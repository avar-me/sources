// sources.avar.me — minimal client-side behavior.

(function () {
  // Auto-collapse page-ToC after navigation on small screens to keep entries
  // visible immediately.
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

  // If we navigated to a #anchor pointing at a <details> (or inside one),
  // open it so the target is actually visible.
  function openDetailsForHash() {
    if (!location.hash) return;
    var id;
    try {
      id = decodeURIComponent(location.hash.slice(1));
    } catch (e) {
      id = location.hash.slice(1);
    }
    var el = document.getElementById(id);
    if (!el) return;
    var d = el.closest ? el.closest("details") : null;
    if (d) d.open = true;
    if (el.tagName && el.tagName.toLowerCase() === "details") el.open = true;
    setTimeout(function () {
      el.scrollIntoView({ block: "start", behavior: "smooth" });
    }, 30);
  }

  document.addEventListener("DOMContentLoaded", function () {
    autoCloseTocOnNav();
    openDetailsForHash();
  });
  window.addEventListener("hashchange", openDetailsForHash);
})();
