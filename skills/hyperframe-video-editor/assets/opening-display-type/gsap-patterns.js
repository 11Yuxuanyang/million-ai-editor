(function registerOpeningTextPatterns(global) {
  "use strict";

  function requireTimeline(timeline) {
    if (!timeline || typeof timeline.fromTo !== "function") {
      throw new TypeError("A GSAP timeline is required.");
    }
  }

  function risePhrase(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const {
      fromY = 160,
      duration = 0.78,
      ease = "expo.out",
      blur = 5,
      scaleFrom = 0.985,
    } = options;
    return timeline.fromTo(
      target,
      { autoAlpha: 0, y: fromY, scale: scaleFrom, filter: `blur(${blur}px)` },
      { autoAlpha: 1, y: 0, scale: 1, filter: "blur(0px)", duration, ease },
      at,
    );
  }

  function sideFade(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const {
      direction = "left",
      distance = 88,
      duration = 0.64,
      ease = "power3.out",
      blur = 6,
    } = options;
    const fromX = direction === "right" ? distance : -distance;
    return timeline.fromTo(
      target,
      { autoAlpha: 0, x: fromX, filter: `blur(${blur}px)` },
      { autoAlpha: 1, x: 0, filter: "blur(0px)", duration, ease },
      at,
    );
  }

  function quietFade(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const { fromY = 22, duration = 0.72, ease = "power2.out" } = options;
    return timeline.fromTo(
      target,
      { autoAlpha: 0, y: fromY },
      { autoAlpha: 1, y: 0, duration, ease },
      at,
    );
  }

  function maskReveal(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const { duration = 0.7, ease = "power4.out", direction = "up" } = options;
    const clipFrom =
      direction === "left"
        ? "inset(0 0 0 100%)"
        : direction === "right"
          ? "inset(0 100% 0 0)"
          : "inset(100% 0 0 0)";
    return timeline.fromTo(
      target,
      { autoAlpha: 1, clipPath: clipFrom },
      { clipPath: "inset(0 0 0 0)", duration, ease },
      at,
    );
  }

  function impactWord(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const { scaleFrom = 1.28, duration = 0.42, ease = "back.out(1.6)" } = options;
    return timeline.fromTo(
      target,
      { autoAlpha: 0, scale: scaleFrom },
      { autoAlpha: 1, scale: 1, duration, ease },
      at,
    );
  }

  function drawStroke(timeline, target, at, options = {}) {
    requireTimeline(timeline);
    const { duration = 0.5, ease = "power2.inOut" } = options;
    return timeline.fromTo(
      target,
      { strokeDasharray: 1, strokeDashoffset: 1 },
      { strokeDashoffset: 0, duration, ease },
      at,
    );
  }

  global.HFOpeningTextPatterns = {
    risePhrase,
    sideFade,
    quietFade,
    maskReveal,
    impactWord,
    drawStroke,
  };
})(typeof window === "undefined" ? globalThis : window);
