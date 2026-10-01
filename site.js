// AM Studio: motion laid over pages that already read complete without this file.
// GSAP, ScrollTrigger, SplitText and Lenis are served from vendor/ (see vendor/LICENSES.md).
(() => {
  const root = document.documentElement;
  const motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;

  // the mobile menu is a popover: a link to this same page should still close it
  const menu = document.getElementById("menu");
  if (menu && menu.hidePopover) {
    menu.addEventListener("click", (e) => {
      if (e.target.closest("a") && menu.matches(":popover-open")) menu.hidePopover();
    });
  }

  /* ---- the section pill: in view after the hero, gone before the footer ---- */
  // not motion, so it is here before the reduced-motion exit; IntersectionObserver, not GSAP

  const pill = document.querySelector(".float-nav");
  const hero = document.querySelector(".hero");
  const footer = document.querySelector(".site-footer");
  if (pill && hero && footer) {
    let pastHero = false, atFooter = false;
    const show = () => pill.classList.toggle("is-on", pastHero && !atFooter);
    new IntersectionObserver(([e]) => { pastHero = !e.isIntersecting && e.boundingClientRect.top < 0; show(); },
      { rootMargin: "-60% 0px 0px 0px" }).observe(hero); // once the hero is above the lower 40% of the window
    new IntersectionObserver(([e]) => { atFooter = e.isIntersecting; show(); }).observe(footer);
    const links = new Map([...pill.querySelectorAll("a")].map((a) => [document.querySelector(a.getAttribute("href")), a]));
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        const a = links.get(e.target);
        e.isIntersecting ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current");
      }
    }, { rootMargin: "-45% 0px -54% 0px" }); // a thin line across the middle of the window
    for (const section of links.keys()) if (section) io.observe(section);
  }

  const g = window.gsap;
  if (!motion || !g || !window.ScrollTrigger) return;
  g.registerPlugin(ScrollTrigger, SplitText);

  /* ---- smooth scrolling, driven by GSAP's clock so ScrollTrigger reads the same position ---- */

  if (window.Lenis) {
    const lenis = new Lenis({ anchors: true });
    lenis.on("scroll", ScrollTrigger.update);
    g.ticker.add((t) => lenis.raf(t * 1000));
    g.ticker.lagSmoothing(0);
  }

  /* ---- things rising into place, out of a blur, as they come into view ---- */

  const from = { up: { y: 55 }, left: { x: -55 }, right: { x: 55 } };
  const reveals = g.utils.toArray("[data-reveal]");
  reveals.forEach((el) => g.set(el, { opacity: 0, filter: "blur(5.6px)", ...from[el.dataset.reveal || "up"] }));
  ScrollTrigger.batch(reveals, {
    start: "top 90%",
    once: true,
    onEnter: (batch) => g.to(batch, {
      opacity: 1, x: 0, y: 0, filter: "blur(0px)",
      duration: 0.9, ease: "power3.out", stagger: 0.08, clearProps: "filter",
    }),
  });

  /* ---- titles that compose word by word ---- */

  const title = document.querySelector(".hero__title, .page-hero h1");
  if (title) {
    const split = SplitText.create(title, { type: "words", wordsClass: "w" });
    g.from(split.words, { opacity: 0, y: 34, filter: "blur(6px)", duration: 0.9, ease: "power3.out", stagger: 0.06 });
  }

  /* ---- the four screens, tilted back, lie flat as the page scrolls ---- */

  const wide = matchMedia("(min-width: 720px)");
  const shots = g.utils.toArray(".showcase__item");
  if (shots.length && wide.matches) {
    const tilt = [26, 9, -9, -26];
    g.from(shots, {
      rotateX: 38, rotateY: (i) => tilt[i % 4], y: 70, z: -140, scale: 0.92,
      transformPerspective: 1400, ease: "none",
      scrollTrigger: { trigger: ".showcase", start: "top 92%", end: "top 20%", scrub: 0.6 },
    });
  }

  /* ---- project spheres orbiting the title ---- */

  const stage = hero && hero.querySelector(".hero__stage");
  const toggle = document.querySelector(".motion-toggle");
  const orbitWide = matchMedia("(min-width: 768px)");
  let startOrbit = () => {}, stopOrbit = () => {};
  if (stage && orbitWide.matches) [startOrbit, stopOrbit] = orbit();

  function orbit() {
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
    let rx = 0, ry = 0, px = 0, py = 0, tx = 0, ty = 0, last = 0, running = false, visible = true;

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
      if (running || !visible || root.classList.contains("is-still")) return;
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

    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      visible ? start() : stop();
    }).observe(hero);
    // a window narrowed below the tablet size goes back to the still composition
    orbitWide.addEventListener("change", (e) => {
      if (e.matches) return;
      stop();
      visible = false;
      hero.classList.remove("is-live");
      for (const b of bodies) {
        b.el.style.transform = b.el.style.zIndex = "";
        if (b.body) b.body.style.opacity = b.haze.style.opacity = "";
      }
    });
    return [start, stop];
  }

  /* ---- one switch stops everything that moves by itself (WCAG 2.2.2) ---- */

  if (toggle) {
    toggle.hidden = false;
    const label = toggle.querySelector("span");
    toggle.addEventListener("click", () => {
      const still = root.classList.toggle("is-still");
      toggle.classList.toggle("is-paused", still);
      label.textContent = still ? toggle.dataset.play : toggle.dataset.pause;
      still ? stopOrbit() : startOrbit();
    });
  }
})();
