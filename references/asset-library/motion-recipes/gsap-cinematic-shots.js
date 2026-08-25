/* Reusable HyperFrames/GSAP shot skeletons. Adapt selectors and geometry per scene. */
(function registerHyperFrameShotLanguage(global) {
  const recipes = {
    snapZoom(tl, selector, time, options = {}) {
      tl.fromTo(selector, {
        scale: options.fromScale ?? 1,
        transformOrigin: options.transformOrigin ?? "50% 44%",
      }, {
        scale: options.toScale ?? options.settle ?? 1.085,
        duration: options.duration ?? 0.72,
        ease: options.ease ?? "expo.out",
      }, time);
    },

    rackFocus(tl, activeSelector, passiveSelector, time, options = {}) {
      tl.to(activeSelector, {
        filter: "blur(0px)",
        opacity: 1,
        scale: options.activeScale ?? 1.04,
        duration: options.duration ?? 0.38,
        ease: "power3.out",
      }, time);
      tl.to(passiveSelector, {
        filter: `blur(${options.passiveBlur ?? 5}px)`,
        opacity: options.passiveOpacity ?? 0.32,
        scale: options.passiveScale ?? 0.98,
        duration: options.duration ?? 0.38,
        ease: "power3.out",
      }, time);
    },

    containerMorph(tl, selectors, time, options = {}) {
      const targets = Array.isArray(selectors) ? selectors.join(",") : selectors;
      tl.to(targets, {
        scale: options.scale ?? 0.46,
        x: options.x ?? 0,
        y: options.y ?? 0,
        borderRadius: options.borderRadius ?? 24,
        transformOrigin: options.transformOrigin ?? "0 0",
        duration: options.duration ?? 0.56,
        ease: "power3.inOut",
      }, time);
    },

    mechanicalShutterTransition(tl, selector, time) {
      tl.fromTo(`${selector} .cut-dark-a`,
        { autoAlpha: 1, xPercent: -112 },
        { autoAlpha: 1, xPercent: 0, duration: 0.095, ease: "power4.in" }, time);
      tl.fromTo(`${selector} .cut-dark-b`,
        { autoAlpha: 1, xPercent: 112 },
        { autoAlpha: 1, xPercent: 0, duration: 0.095, ease: "power4.in" }, time);
      tl.to(`${selector} .cut-dark-a`,
        { xPercent: -112, duration: 0.125, ease: "power4.out" }, time + 0.095);
      tl.to(`${selector} .cut-dark-b`,
        { xPercent: 112, duration: 0.125, ease: "power4.out" }, time + 0.095);
      tl.fromTo(`${selector} .cut-light`,
        { autoAlpha: 0, scaleY: 0.3 },
        { autoAlpha: 1, scaleY: 1, duration: 0.025, ease: "power2.out" }, time + 0.082);
      tl.to(`${selector} .cut-light`,
        { autoAlpha: 0, scaleY: 0.45, duration: 0.07, ease: "power2.in" }, time + 0.12);
    },

    presenterCardOrbit(tl, selector, time, options = {}) {
      const cards = gsap.utils.toArray(selector);
      const poses = options.poses || [
        { x: -420, y: 100, z: -90, rotateY: 28, rotateZ: -6, scale: 0.86 },
        { x: -230, y: 10, z: 30, rotateY: 16, rotateZ: -2, scale: 0.94 },
        { x: 230, y: 10, z: 30, rotateY: -16, rotateZ: 2, scale: 0.94 },
        { x: 420, y: 100, z: -90, rotateY: -28, rotateZ: 6, scale: 0.86 },
      ];

      gsap.set(options.stage || cards[0]?.parentElement, {
        perspective: options.perspective ?? 1400,
        transformStyle: "preserve-3d",
      });

      cards.forEach((card, index) => {
        tl.fromTo(card, {
          x: options.originX ?? 0,
          y: options.originY ?? 90,
          z: options.originZ ?? -260,
          rotateY: 0,
          rotateZ: 0,
          scale: options.originScale ?? 0.54,
          autoAlpha: 0,
        }, {
          ...(poses[index] || poses[poses.length - 1]),
          autoAlpha: 1,
          duration: options.duration ?? 0.58,
          ease: options.ease ?? "power4.out",
        }, time + index * (options.stagger ?? 0.14));
      });
    },
  };

  // Compatibility aliases for projects authored before the terminology cleanup.
  recipes.snapPush = recipes.snapZoom;
  recipes.transferFocus = recipes.rackFocus;
  recipes.shrinkToScene = recipes.containerMorph;
  recipes.mechanicalLightShutter = recipes.mechanicalShutterTransition;

  global.HFShotLanguage = Object.assign(global.HFShotLanguage || {}, recipes);
})(window);
