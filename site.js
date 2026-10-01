// AM Studio: motion and controls laid over pages that already read complete without this file.
(() => {
  const motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- project spheres orbiting the title ---- */

  const hero = document.querySelector(".hero");
  const stage = hero && hero.querySelector(".hero__stage");
  const wide = matchMedia("(min-width: 768px)");
  if (stage && motion && wide.matches) orbit();

  function orbit() {
    const toggle = hero.querySelector(".orbit-toggle");
    const bodies = [...stage.querySelectorAll(".orb, .speck")].map((el) => {
      const speck = el.classList.contains("speck");
      return {
        el, speck,
        a: parseFloat(el.style.getPropertyValue("--a")) * Math.PI / 180,
        k: speck ? parseFloat(getComputedStyle(el).getPropertyValue("--k")) || 1.3 : 1,
        w: speck ? 0.035 : 0.06, // radians a second: one turn in under two minutes
        body: el.querySelector(".orb__body"),
        haze: el.querySelector(".orb__haze"),
      };
    });
    const held = new Set(); // spheres under the pointer or the keyboard focus stay where they are
    let rx = 0, ry = 0, px = 0, py = 0, tx = 0, ty = 0, last = 0, running = false, paused = false;

    const measure = () => {
      const style = getComputedStyle(stage);
      rx = parseFloat(style.getPropertyValue("--rx"));
      ry = parseFloat(style.getPropertyValue("--ry"));
    };
    measure();
    addEventListener("resize", measure);
    hero.classList.add("is-live");

    function frame(now) {
      const dt = Math.min(now - last, 50) / 1000;
      last = now;
      px += (tx - px) * 0.05;
      py += (ty - py) * 0.05;
      for (const b of bodies) {
        if (!held.size) b.a += b.w * dt;
        const z = Math.sin(b.a); // -1 behind the title, 1 in front of it
        const k = (z + 1) / 2;
        const x = Math.cos(b.a) * rx * b.k - px * (12 + 40 * k);
        const y = z * ry * b.k - py * (8 + 24 * k);
        b.el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) scale(${(0.72 + 0.4 * k).toFixed(3)})`;
        if (b.speck) continue;
        b.el.style.zIndex = z > 0 ? 3 : 1;
        b.body.style.opacity = (0.3 + 0.7 * k).toFixed(3);
        b.haze.style.opacity = (1 - k).toFixed(3);
      }
      if (running) requestAnimationFrame(frame);
    }
    const start = () => {
      if (running || paused) return;
      running = true;
      last = performance.now();
      requestAnimationFrame(frame);
    };
    const stop = () => { running = false; };

    for (const b of bodies) {
      if (b.speck) continue;
      b.el.addEventListener("pointerenter", () => held.add(b.el));
      b.el.addEventListener("pointerleave", () => held.delete(b.el));
      b.el.addEventListener("focusin", () => held.add(b.el));
      b.el.addEventListener("focusout", () => held.delete(b.el));
    }
    hero.addEventListener("pointermove", (e) => {
      if (e.pointerType !== "mouse") return;
      tx = e.clientX / innerWidth - 0.5;
      ty = e.clientY / innerHeight - 0.5;
    });
    // the gyroscope only where it comes without a permission prompt: not worth one for a decoration
    if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission !== "function") {
      const clamp = (v) => Math.max(-0.5, Math.min(0.5, v));
      addEventListener("deviceorientation", (e) => {
        if (e.gamma == null) return;
        tx = clamp(e.gamma / 40);
        ty = clamp((e.beta - 40) / 40);
      });
    }

    // moving content needs a way to stop it (WCAG 2.2.2)
    toggle.hidden = false;
    const label = toggle.querySelector("span");
    toggle.addEventListener("click", () => {
      paused = !paused;
      toggle.classList.toggle("is-paused", paused);
      label.textContent = paused ? toggle.dataset.play : toggle.dataset.pause;
      paused ? stop() : start();
    });

    new IntersectionObserver(([entry]) => (entry.isIntersecting ? start() : stop())).observe(hero);
    // a window narrowed below the tablet size goes back to the still composition
    wide.addEventListener("change", (e) => {
      if (e.matches) return;
      paused = true;
      stop();
      toggle.hidden = true;
      hero.classList.remove("is-live");
      for (const b of bodies) {
        b.el.style.transform = b.el.style.zIndex = "";
        if (b.body) b.body.style.opacity = b.haze.style.opacity = "";
      }
    });
  }

  /* ---- numbers counting up, the ring drawn with them ---- */

  const panel = document.querySelector(".stats__glass");
  if (panel && motion && "IntersectionObserver" in window) {
    const numbers = [...panel.querySelectorAll("[data-count]")];
    const arcs = [...panel.querySelectorAll("[data-ring]")];
    numbers.forEach((n) => (n.textContent = "0"));
    arcs.forEach((a) => a.style.setProperty("--p", 0));
    const io = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      requestAnimationFrame(function tick(now) {
        const t = Math.min((now - t0) / 1600, 1);
        const e = 1 - (1 - t) ** 3; // one progress for numbers and arc, so they finish together
        numbers.forEach((n) => (n.textContent = Math.round(e * n.dataset.count)));
        arcs.forEach((a) => a.style.setProperty("--p", (e * a.dataset.ring).toFixed(4)));
        if (t < 1) requestAnimationFrame(tick);
      });
    }, { threshold: 0.45 });
    io.observe(panel);
  }

  /* ---- the GesTeach views: accordion and tabs are two ways to one choice ---- */

  const views = document.querySelector("[data-views]");
  if (views) {
    const tablist = views.querySelector(".tabs");
    const tabs = [...tablist.querySelectorAll(".tab")];
    const screen = views.querySelector(".screen__inner");
    const shots = [...screen.querySelectorAll(".shot")];
    const heads = [...views.querySelectorAll(".acc__btn")];

    tablist.hidden = false;
    tablist.setAttribute("role", "tablist");
    tablist.setAttribute("aria-label", tablist.dataset.label);
    screen.setAttribute("role", "tabpanel");
    screen.tabIndex = 0;
    tabs.forEach((t) => {
      t.setAttribute("role", "tab");
      t.setAttribute("aria-controls", screen.id);
    });

    const select = (key, focus) => {
      for (const t of tabs) {
        const on = t.dataset.key === key;
        t.setAttribute("aria-selected", on);
        t.tabIndex = on ? 0 : -1;
        if (on) screen.setAttribute("aria-labelledby", t.id);
        if (on && focus) t.focus();
      }
      for (const s of shots) {
        const on = s.dataset.key === key;
        if (on && s.hidden) {
          s.classList.remove("is-new");
          void s.offsetWidth; // restart the opening line
          s.classList.add("is-new");
        }
        s.hidden = !on;
      }
      for (const h of heads) {
        const on = h.dataset.key === key;
        h.setAttribute("aria-expanded", on);
        // one entry is always open, so the open one cannot be closed (APG accordion)
        if (on) h.setAttribute("aria-disabled", "true");
        else h.removeAttribute("aria-disabled");
        document.getElementById(h.getAttribute("aria-controls")).hidden = !on;
      }
    };

    tabs.forEach((t) => t.addEventListener("click", () => select(t.dataset.key)));
    heads.forEach((h) => h.addEventListener("click", () => select(h.dataset.key)));
    tablist.addEventListener("keydown", (e) => {
      const i = tabs.indexOf(document.activeElement);
      const to = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (i < 0 || to === undefined) return;
      e.preventDefault();
      select(tabs[(to + tabs.length) % tabs.length].dataset.key, true);
    });
    select(tabs[0].dataset.key);
  }
})();
