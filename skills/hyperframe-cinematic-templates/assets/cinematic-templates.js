/* Copy into a HyperFrame project and adapt geometry to the actual presenter. */
(function registerHFCinematicTemplates(global) {
  const motion = global.gsap;

  function targets(value) {
    if (typeof value === "string") return motion.utils.toArray(value);
    if (!value) return [];
    if (value.nodeType === 1 || value === global) return [value];
    return Array.from(value);
  }

  function at(value, fallback) {
    return value ?? fallback;
  }

  const api = {
    presenterCardOrbit(tl, cards, time, options = {}) {
      const items = targets(cards);
      const poses = options.poses || [
        { x: -420, y: 100, z: -90, rotateY: 28, rotateZ: -6, scale: 0.86 },
        { x: -230, y: 10, z: 30, rotateY: 16, rotateZ: -2, scale: 0.94 },
        { x: 230, y: 10, z: 30, rotateY: -16, rotateZ: 2, scale: 0.94 },
        { x: 420, y: 100, z: -90, rotateY: -28, rotateZ: 6, scale: 0.86 }
      ];

      const stage = options.stage || items[0]?.parentElement;
      if (stage) {
        motion.set(stage, {
          perspective: at(options.perspective, 1400),
          transformStyle: "preserve-3d"
        });
      }

      items.forEach((card, index) => {
        const pose = poses[index] || poses[poses.length - 1];
        tl.fromTo(card, {
          x: at(options.originX, 0),
          y: at(options.originY, 90),
          z: at(options.originZ, -260),
          rotateY: 0,
          rotateZ: 0,
          scale: at(options.originScale, 0.54),
          autoAlpha: 0
        }, {
          ...pose,
          autoAlpha: 1,
          duration: at(options.duration, 0.58),
          ease: at(options.ease, "power4.out")
        }, time + index * at(options.stagger, 0.14));
      });
    },

    sharedPivotPageFan(tl, cards, time, options = {}) {
      const items = targets(cards);
      const center = (items.length - 1) / 2;
      items.forEach((card, index) => {
        const offset = index - center;
        tl.fromTo(card, {
          x: 0,
          y: at(options.originY, 120),
          z: -160,
          rotateY: 0,
          rotateZ: 0,
          autoAlpha: 0,
          transformOrigin: "50% 100%"
        }, {
          x: offset * at(options.spacing, 210),
          y: Math.abs(offset) * at(options.drop, 34),
          z: -Math.abs(offset) * at(options.depth, 44),
          rotateY: -offset * at(options.yaw, 12),
          rotateZ: offset * at(options.fan, 7),
          autoAlpha: 1,
          duration: at(options.duration, 0.7),
          ease: at(options.ease, "power4.out")
        }, time + Math.abs(offset) * 0.05);
      });
    },

    longTailScale(tl, target, time, options = {}) {
      tl.fromTo(target, {
        scale: at(options.fromScale, 1),
        x: at(options.fromX, 0),
        y: at(options.fromY, 0),
        transformOrigin: at(options.transformOrigin, "50% 44%")
      }, {
        scale: at(options.toScale, 1.1),
        x: at(options.toX, 0),
        y: at(options.toY, 0),
        duration: at(options.duration, 0.72),
        ease: at(options.ease, "expo.out")
      }, time);
    },

    layeredDisplayType(tl, layers, time, options = {}) {
      const items = targets(layers);
      items.forEach((item, index) => {
        const pose = options.poses?.[index] || {};
        tl.fromTo(item, {
          autoAlpha: 0,
          y: at(pose.fromY, at(options.fromY, 54)),
          scale: at(pose.fromScale, at(options.fromScale, 0.96)),
          filter: at(pose.fromFilter, "blur(0px)")
        }, {
          autoAlpha: at(pose.opacity, 1),
          y: at(pose.y, 0),
          scale: at(pose.scale, 1),
          filter: at(pose.filter, "blur(0px)"),
          duration: at(pose.duration, at(options.duration, 0.42)),
          ease: at(pose.ease, at(options.ease, "power4.out"))
        }, time + index * at(options.stagger, 0.12));
      });
    },

    cueLockedEvidenceHandoff(tl, presenter, evidence, time, options = {}) {
      tl.to(presenter, {
        autoAlpha: at(options.presenterOpacity, 0),
        scale: at(options.presenterScale, 1),
        duration: at(options.outDuration, 0.18),
        ease: at(options.outEase, "power3.in")
      }, time);
      tl.fromTo(evidence, {
        autoAlpha: 0,
        scale: at(options.evidenceFromScale, 1.035),
        y: at(options.evidenceFromY, 18)
      }, {
        autoAlpha: 1,
        scale: 1,
        y: 0,
        duration: at(options.inDuration, 0.34),
        ease: at(options.inEase, "power4.out")
      }, time + at(options.overlap, 0.06));
    },

    fullFrameToPipHandoff(tl, evidence, time, options = {}) {
      const destination = options.destination || {};
      tl.fromTo(evidence, {
        x: at(options.fromX, 0),
        y: at(options.fromY, 0),
        width: at(options.fromWidth, "100%"),
        height: at(options.fromHeight, "100%"),
        borderRadius: at(options.fromRadius, 0),
        transformOrigin: at(options.transformOrigin, "50% 50%")
      }, {
        x: at(destination.x, 0),
        y: at(destination.y, 0),
        width: at(destination.width, 480),
        height: at(destination.height, 300),
        borderRadius: at(destination.borderRadius, 18),
        duration: at(options.duration, 0.72),
        ease: at(options.ease, "expo.out")
      }, time);
    },

    quickFlashMontage(tl, frames, time, options = {}) {
      const items = targets(frames);
      const hold = at(options.hold, 0.11);
      items.forEach((frame, index) => {
        tl.set(frame, { autoAlpha: 1, scale: at(options.scale, 1.025) },
          time + index * hold);
        tl.set(frame, { autoAlpha: 0 },
          time + (index + 1) * hold);
      });
    },

    scatterIndexRetrieve(tl, items, time, options = {}) {
      const nodes = targets(items);
      const slots = options.slots || [];
      nodes.forEach((item, index) => {
        const start = options.starts?.[index] || {};
        const slot = slots[index] || {};
        tl.fromTo(item, {
          x: at(start.x, 0),
          y: at(start.y, 0),
          rotate: at(start.rotate, 0),
          scale: at(start.scale, 1),
          autoAlpha: at(start.opacity, 1)
        }, {
          x: at(slot.x, 0),
          y: at(slot.y, 0),
          rotate: at(slot.rotate, 0),
          scale: at(slot.scale, 1),
          autoAlpha: 1,
          duration: at(options.indexDuration, 0.58),
          ease: at(options.indexEase, "power3.inOut")
        }, time + index * at(options.indexStagger, 0.06));
      });

      const selected = nodes[at(options.retrieveIndex, 0)];
      if (selected) {
        tl.to(selected, {
          x: at(options.retrieve?.x, 0),
          y: at(options.retrieve?.y, 0),
          scale: at(options.retrieve?.scale, 1.12),
          zIndex: at(options.retrieve?.zIndex, 20),
          duration: at(options.retrieveDuration, 0.5),
          ease: at(options.retrieveEase, "expo.out")
        }, time + at(options.retrieveAt, 1));
      }
    },

    generatedCutoutSequence(tl, pieces, time, options = {}) {
      const items = targets(pieces);
      items.forEach((piece, index) => {
        const enter = options.enters?.[index] || {};
        const action = options.actions?.[index];
        const start = time + at(enter.delay, index * at(options.stagger, 0.12));
        tl.fromTo(piece, {
          x: at(enter.fromX, 0),
          y: at(enter.fromY, 24),
          scale: at(enter.fromScale, 0.86),
          rotate: at(enter.fromRotate, 0),
          autoAlpha: 0
        }, {
          x: at(enter.x, 0),
          y: at(enter.y, 0),
          scale: at(enter.scale, 1),
          rotate: at(enter.rotate, 0),
          autoAlpha: 1,
          duration: at(enter.duration, at(options.enterDuration, 0.4)),
          ease: at(enter.ease, at(options.enterEase, "power4.out"))
        }, start);
        if (action) {
          tl.to(piece, {
            ...action.vars,
            duration: at(action.duration, 0.36),
            ease: at(action.ease, "power2.inOut")
          }, time + at(action.at, 0.72));
        }
      });
    },

    containerMorph(tl, elements, time, options = {}) {
      const items = targets(elements);
      tl.to(items, {
        x: at(options.x, 0),
        y: at(options.y, 0),
        scale: at(options.scale, 0.48),
        borderRadius: at(options.borderRadius, 20),
        duration: at(options.duration, 0.62),
        ease: at(options.ease, "power3.inOut"),
        transformOrigin: at(options.transformOrigin, "50% 50%")
      }, time);
    },

    rackFocus(tl, active, passive, time, options = {}) {
      tl.to(active, {
        filter: "blur(0px)",
        opacity: 1,
        scale: at(options.activeScale, 1.03),
        duration: at(options.duration, 0.38),
        ease: at(options.ease, "power3.out")
      }, time);
      tl.to(passive, {
        filter: `blur(${at(options.passiveBlur, 5)}px)`,
        opacity: at(options.passiveOpacity, 0.34),
        scale: at(options.passiveScale, 0.99),
        duration: at(options.duration, 0.38),
        ease: at(options.ease, "power3.out")
      }, time);
    },

    brushAccent(tl, stroke, time, options = {}) {
      tl.fromTo(stroke, {
        clipPath: "inset(0 100% 0 0)",
        autoAlpha: 1
      }, {
        clipPath: "inset(0 0% 0 0)",
        duration: at(options.duration, 0.38),
        ease: "power3.out"
      }, time);
    },

    exposureFlash(tl, overlay, time, options = {}) {
      tl.fromTo(overlay, { autoAlpha: 0 }, {
        autoAlpha: at(options.peakOpacity, 0.96),
        duration: at(options.rise, 0.07),
        ease: "power3.in"
      }, time);
      tl.to(overlay, {
        autoAlpha: 0,
        duration: at(options.fall, 0.16),
        ease: "power3.out"
      }, time + at(options.rise, 0.07));
    }
  };

  api.snapZoom = api.longTailScale;
  api.snapPullback = api.longTailScale;

  global.HFCinematicTemplates = Object.assign(
    global.HFCinematicTemplates || {},
    api
  );
})(window);
