// AM Studio: a project's sphere opens into the project's page, and the page closes back into it.
// Cross-document view transitions: Chrome, Edge, Safari 18.2+. Anywhere else, and with reduced
// motion, a sphere is an ordinary link. Loaded in <head> and not deferred, because pagereveal comes
// before the first frame and a listener added any later misses it.
(() => {
  const root = document.documentElement;
  if (!("onpagereveal" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const KEY = "am-zoom"; // what the page on the other side needs to know: which sphere, and where
  const EASE = "cubic-bezier(.65, 0, .25, 1)";
  // only the pages that load this file take part, so every other navigation stays a plain one
  const style = document.createElement("style");
  style.textContent = `@view-transition { navigation: auto; }
::view-transition-old(root), ::view-transition-new(root) { animation: none; mix-blend-mode: normal; }
.zoom-out::view-transition-old(root) { z-index: 1; }`;
  document.head.append(style);

  const page = (href) => new URL(href, location.href).pathname.replace(/index\.html$/, "");
  const isHome = () => document.body?.classList.contains("home");
  const save = (record) => {
    try { sessionStorage.setItem(KEY, JSON.stringify({ ...record, t: Date.now() })); } catch {}
  };
  const take = () => {
    try {
      const record = JSON.parse(sessionStorage.getItem(KEY));
      sessionStorage.removeItem(KEY);
      return record && Date.now() - record.t < 30000 ? record : null;
    } catch { return null; }
  };
  const traversed = () => window.navigation && navigation.activation
    ? navigation.activation.navigationType === "traverse"
    : performance.getEntriesByType("navigation")[0]?.type === "back_forward";

  let played = [], leaving = false, viaButton = false;

  addEventListener("click", (e) => {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const link = e.target.closest?.(".orb__link[href], a.back");
    if (!link) return;

    if (link.classList.contains("back")) {
      // came from the home: go back the way we came, so the history stays as it was
      if (document.referrer && page(document.referrer) === page(link.href)) {
        e.preventDefault();
        history.back();
      } else viaButton = true;
      return;
    }

    // the other spheres fade and this one swells, then the page opens out of it
    e.preventDefault();
    if (leaving) return;
    leaving = true;
    root.classList.add("is-zooming"); // site.js: the orbit stops turning
    const orb = link.closest(".orb");
    const timing = { duration: 500, easing: "ease-in-out", fill: "forwards" };
    played = [...document.querySelectorAll(".site-header, .hero__mark, .hero__hint, .particles, .orb, .orb__desc, .motion-toggle")]
      .filter((el) => el !== orb)
      .map((el) => el.animate({ opacity: 0 }, timing));
    played.push(link.animate({ scale: 1.5 }, timing));
    Promise.all(played.map((a) => a.finished)).then(() => {
      const box = link.getBoundingClientRect();
      save({ dir: "in", to: page(link.href), x: box.left + box.width / 2, y: box.top + box.height / 2, r: box.width / 2 });
      location.href = link.href;
    });
  });

  // leaving a project page leaves a trail, so the home can close the page back into its sphere
  addEventListener("pageswap", () => {
    if (isHome()) return;
    save({ dir: "out", from: page(location.href), via: viaButton });
    viaButton = false;
  });

  addEventListener("pagereveal", (e) => {
    // a home restored from the back/forward cache comes back as it was left, spheres faded
    for (const a of played) a.cancel();
    played = [];
    leaving = false;
    root.classList.remove("is-zooming");

    const record = take();
    const vt = e.viewTransition;
    if (!vt) return;
    if (isHome() && record?.dir === "out" && (record.via || traversed())) {
      const link = [...document.querySelectorAll(".orb__link[href]")].find((a) => page(a.href) === record.from);
      const box = link?.getBoundingClientRect();
      if (box && box.bottom > 0 && box.top < innerHeight) {
        return zoom(vt, { x: box.left + box.width / 2, y: box.top + box.height / 2, r: box.width / 2 }, true);
      }
    }
    if (!isHome() && record?.dir === "in" && record.to === page(location.href)) return zoom(vt, record, false);
    vt.ready.catch(() => {}); // a skipped transition rejects ready: expected, not an error
    vt.skipTransition(); // the logo, the menu, the language switch: plain navigations
  });

  // in: the new page shows through a circle the size of the sphere, which grows to the window while
  // the home swells around the same point, so the sphere's rim rides the circle's edge. Out: the same,
  // played backwards, with the project page on top
  function zoom(vt, { x, y, r }, out) {
    const far = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    const at = `at ${x}px ${y}px`, origin = `${x}px ${y}px`;
    // the page comes up inside the sphere first, so the sphere is still a sphere when it starts to grow
    const circle = [
      { clipPath: `circle(${r}px ${at})`, opacity: 0 },
      { opacity: 1, offset: 0.25 },
      { clipPath: `circle(${far}px ${at})`, opacity: 1 },
    ];
    const swell = [
      { transformOrigin: origin, transform: "none", opacity: 1 },
      { opacity: 1, offset: 0.3 },
      { transformOrigin: origin, transform: `scale(${far / r})`, opacity: 0 },
    ];
    const timing = { duration: out ? 1200 : 1000, easing: EASE, fill: "both", direction: out ? "reverse" : "normal" };
    root.classList.add("is-zooming");
    root.classList.toggle("zoom-out", out);
    vt.ready.then(() => {
      root.animate(circle, { ...timing, pseudoElement: `::view-transition-${out ? "old" : "new"}(root)` });
      root.animate(swell, { ...timing, pseudoElement: `::view-transition-${out ? "new" : "old"}(root)` });
    }).catch(() => {});
    vt.finished.finally(() => root.classList.remove("is-zooming", "zoom-out"));
  }
})();
