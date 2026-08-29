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

    parallelInterfaceSwarm(tl, selector, time, options = {}) {
      const panels = gsap.utils.toArray(selector);
      if (!panels.length) return;
      const minPanels = options.minPanels ?? 6;
      if (panels.length < minPanels) {
        throw new Error(`parallelInterfaceSwarm requires at least ${minPanels} panels`);
      }

      const stage = typeof options.stage === "string"
        ? document.querySelector(options.stage)
        : (options.stage || panels[0].parentElement);
      if (!stage) throw new Error("parallelInterfaceSwarm requires a stage element");
      const duration = options.duration ?? 2.4;
      const starts = options.starts || [
        { x: 82, y: 62, z: -220, rx: 10, ry: -15, rz: -7, at: 0.00, enter: 0.46 },
        { x: -280, y: 160, z: -190, rx: 13, ry: 33, rz: 18, at: 0.08, enter: 0.64 },
        { x: 300, y: 178, z: -160, rx: -8, ry: -39, rz: -19, at: 0.16, enter: 0.62 },
        { x: -190, y: -190, z: -520, rx: -20, ry: 27, rz: -19, at: 0.04, enter: 0.72 },
        { x: 190, y: -210, z: -560, rx: 20, ry: -25, rz: 21, at: 0.22, enter: 0.70 },
        { x: 30, y: 260, z: -380, rx: 28, ry: -10, rz: 13, at: 0.13, enter: 0.66 },
        { x: -360, y: -80, z: -650, rx: 9, ry: 35, rz: 26, at: 0.18, enter: 0.74 },
        { x: 390, y: -80, z: -620, rx: -17, ry: -32, rz: -25, at: 0.25, enter: 0.70 },
        { x: 0, y: -300, z: -760, rx: -25, ry: 8, rz: 12, at: 0.11, enter: 0.78 },
      ];
      const drifts = options.drifts || [
        { x: -66, y: -24, z: 42, rx: -1, ry: 3, rz: -1 },
        { x: 52, y: -72, z: -18, rx: -2, ry: -4, rz: -2 },
        { x: -78, y: -54, z: 28, rx: 2, ry: 5, rz: 2 },
        { x: 58, y: 42, z: 22, rx: 1, ry: -3, rz: 2 },
        { x: -42, y: 54, z: 12, rx: -1, ry: 4, rz: -3 },
        { x: 34, y: -68, z: 35, rx: -3, ry: 2, rz: -2 },
        { x: 76, y: 48, z: 18, rx: 2, ry: -5, rz: -3 },
        { x: -68, y: 36, z: 26, rx: 1, ry: 4, rz: 4 },
        { x: 40, y: 88, z: 20, rx: 3, ry: -2, rz: -2 },
      ];
      const initialCamera = options.initialCamera || {
        x: 86, y: 54, scale: 0.90,
        rotationX: 8, rotationY: -11, rotationZ: -2,
      };
      const passCamera = options.passCamera || {
        x: -108, y: -52, scale: 1.055,
        rotationX: -4, rotationY: 7, rotationZ: 2,
      };
      const landingCamera = options.landingCamera || {
        x: -172, y: -84, scale: 1.14,
        rotationX: -1.5, rotationY: 3, rotationZ: -1,
      };

      tl.set(stage, {
        ...initialCamera,
        transformPerspective: options.perspective ?? 1560,
        transformStyle: "preserve-3d",
      }, time);

      panels.forEach((panel, index) => {
        const start = starts[index % starts.length];
        const drift = drifts[index % drifts.length];
        const target = {
          x: Number(panel.dataset.x || 0),
          y: Number(panel.dataset.y || 0),
          z: Number(panel.dataset.z || 0),
          rotationX: Number(panel.dataset.rx || 0),
          rotationY: Number(panel.dataset.ry || 0),
          rotationZ: Number(panel.dataset.rz || 0),
        };
        const entranceEnd = start.at + start.enter;

        tl.fromTo(panel, {
          autoAlpha: index === 0 ? 0.82 : (index < 6 ? 0.16 : 0.08),
          x: start.x,
          y: start.y,
          z: start.z,
          rotationX: start.rx,
          rotationY: start.ry,
          rotationZ: start.rz,
          scale: index === 0 ? 0.88 : 0.72,
        }, {
          autoAlpha: 1,
          ...target,
          scale: 1,
          duration: start.enter,
          ease: options.entranceEase ?? "power4.out",
        }, time + start.at);

        tl.to(panel, {
          x: target.x + drift.x,
          y: target.y + drift.y,
          z: target.z + drift.z,
          rotationX: target.rotationX + drift.rx,
          rotationY: target.rotationY + drift.ry,
          rotationZ: target.rotationZ + drift.rz,
          duration: Math.max(0.01, duration - entranceEnd),
          ease: options.driftEase ?? "sine.inOut",
        }, time + entranceEnd);

        const media = panel.querySelector(options.mediaSelector || ".media");
        if (media) {
          const direction = index % 2 === 0 ? 1 : -1;
          tl.fromTo(media, {
            xPercent: -direction * (1.0 + (index % 3) * 0.35),
            yPercent: direction * 0.6,
            scale: options.mediaFromScale ?? 1.055,
          }, {
            xPercent: direction * (1.4 + (index % 4) * 0.28),
            yPercent: -direction * 0.8,
            scale: options.mediaToScale ?? 1.10,
            duration,
            ease: "sine.inOut",
          }, time);
        }

        const playhead = panel.querySelector(options.playheadSelector || ".playhead");
        if (playhead) {
          const width = playhead.parentElement?.offsetWidth || panel.offsetWidth || 640;
          const from = width * (12 + (index * 5) % 24) / 100;
          const to = width * (70 + (index * 3) % 18) / 100;
          tl.fromTo(playhead, { x: from }, {
            x: to,
            duration: Math.max(0.2, duration - 0.20 - index * 0.035),
            ease: "none",
          }, time + 0.08 + index * 0.018);
        }
      });

      const firstLeg = duration * (options.firstLegRatio ?? 0.65);
      tl.to(stage, {
        ...passCamera,
        duration: firstLeg,
        ease: options.firstLegEase ?? "power2.inOut",
      }, time);
      tl.to(stage, {
        ...landingCamera,
        duration: duration - firstLeg,
        ease: options.landingEase ?? "power3.out",
      }, time + firstLeg);

      const pulseSelector = options.pulseSelector || `${selector} .edit-pulse`;
      if (options.pulse !== false && document.querySelector(pulseSelector)) {
        tl.to(pulseSelector, {
          boxShadow: options.pulseBoxShadow
            ?? "0 0 0 13px rgba(255,210,56,0), 0 0 18px rgba(255,210,56,.42)",
          duration: options.pulseDuration ?? 0.44,
          repeat: options.pulseRepeat ?? 4,
          ease: "power2.out",
          stagger: { each: options.pulseStagger ?? 0.035, from: "random" },
        }, time + 0.12);
      }
    },
  };

  // Compatibility aliases for projects authored before the terminology cleanup.
  recipes.snapPush = recipes.snapZoom;
  recipes.transferFocus = recipes.rackFocus;
  recipes.shrinkToScene = recipes.containerMorph;
  recipes.mechanicalLightShutter = recipes.mechanicalShutterTransition;

  global.HFShotLanguage = Object.assign(global.HFShotLanguage || {}, recipes);
})(window);
