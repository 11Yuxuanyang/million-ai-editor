window.__timelines = window.__timelines || {};

const tl = gsap.timeline({ paused: true });
const fast = "power4.out";
const settle = "power3.out";

function reveal(target, at, from = {}, to = {}) {
  tl.fromTo(
    target,
    { autoAlpha: 0, ...from },
    { autoAlpha: 1, duration: 0.42, ease: fast, ...to },
    at,
  );
}

function hide(target, at, to = {}) {
  tl.to(target, { autoAlpha: 0, duration: 0.24, ease: "power2.in", ...to }, at);
}

const pixelField = document.querySelector(".pixel-field");
if (pixelField && pixelField.children.length === 0) {
  for (let index = 0; index < 240; index += 1) {
    pixelField.appendChild(document.createElement("i"));
  }
}

// Camera language: every push or pull lands and holds until the next source cut.
tl.set("#a-roll, #opening-cutout", {
  scale: 1.13,
  transformOrigin: "50% 48%",
}, 0);
tl.to("#a-roll, #opening-cutout", {
  scale: 1,
  duration: 1.18,
  ease: fast,
}, 0.03);
tl.to("#a-roll", { scale: 1.055, duration: 0.3, ease: fast }, 20.62);
tl.set("#a-roll", { scale: 1 }, 24.8727);
tl.to("#a-roll", { scale: 1.075, duration: 0.32, ease: fast }, 26.1);
tl.set("#a-roll", { scale: 1 }, 33.5273);
tl.to("#a-roll", { scale: 1.052, duration: 0.72, ease: "power3.out" }, 43.72);
tl.set("#a-roll", { scale: 1 }, 45.32);
tl.to("#a-roll", { scale: 1.085, duration: 0.28, ease: fast }, 51.42);
tl.set("#a-roll", { scale: 1 }, 55.12);
tl.to("#a-roll", { scale: 1.06, duration: 0.34, ease: fast }, 61.5273);
tl.set("#a-roll", { scale: 1 }, 64.1091);

// 0-3.8s: no body captions. Foreground thesis, subject, then oversized answer behind.
tl.set(".opening-minor span, .opening-hero, .opening-kicker, .opening-corner", { autoAlpha: 0 }, 0);
reveal(".opening-kicker", 0.08, { y: 92, scale: 0.9 }, { y: 0, scale: 1, duration: 0.5 });
reveal(".opening-minor span:first-child", 0.48, { x: -55 }, { x: 0, duration: 0.34 });
reveal(".opening-minor span:last-child", 0.67, { x: -55 }, { x: 0, duration: 0.34 });
tl.fromTo(".opening-minor i", { scaleX: 0 }, {
  scaleX: 1,
  duration: 0.34,
  stagger: 0.06,
  ease: "power3.out",
}, 1.24);
hide(".opening-minor", 1.75, { y: -18 });
reveal(".opening-hero", 1.62, { y: 105, scale: 0.79 }, {
  y: 0,
  scale: 1,
  duration: 0.62,
});
reveal(".opening-corner", 2.1, { x: 70 }, { x: 0, duration: 0.38 });

// 3.8-8.1s: the recurring question arrives like a task handed back to the founder.
tl.set(".question-echo, .question-main", { autoAlpha: 0 }, 0);
reveal(".question-echo-a", 4.08, { x: 120, scale: 0.78 }, { x: 0, scale: 0.84, duration: 0.38 });
reveal(".question-echo-b", 4.32, { x: 120, scale: 0.84 }, { x: 0, scale: 0.92, duration: 0.38 });
reveal(".question-main", 4.72, { x: 145, rotateY: -11 }, {
  x: 0,
  rotateY: 0,
  duration: 0.52,
});
hide(".question-echo", 6.9, { x: 40 });

// 8.2-21.4s: real editorial footage establishes where knowledge actually lives.
tl.fromTo("#voice-note-broll", { scale: 1.09 }, {
  scale: 1,
  duration: 2.94,
  ease: "power2.out",
}, 8.18);
tl.fromTo("#voice-note-label", { autoAlpha: 0, y: 45 }, {
  autoAlpha: 1,
  y: 0,
  duration: 0.42,
  ease: fast,
}, 8.28);
tl.fromTo("#team-computers-broll", { scale: 1 }, {
  scale: 1.045,
  duration: 1.60,
  ease: "power2.out",
}, 11.12);
tl.fromTo("#team-computers-label", { autoAlpha: 0, x: 70 }, {
  autoAlpha: 1,
  x: 0,
  duration: 0.3,
  ease: fast,
}, 11.2);
tl.set("#office-work-broll", {
  x: 0,
  y: 0,
  borderRadius: 0,
  scale: 1,
}, 15.18);
tl.fromTo("#office-work-broll", { scale: 1.045 }, { scale: 1, duration: 3.08, ease: "power2.out" }, 15.18);
tl.fromTo("#office-work-label", { autoAlpha: 0, y: 45 }, {
  autoAlpha: 1,
  y: 0,
  duration: 0.42,
  ease: fast,
}, 15.3);
tl.to("#office-work-label", { autoAlpha: 0, duration: 0.24 }, 18.28);
tl.to("#office-work-broll", {
  x: -90,
  y: 92,
  scale: 0.292,
  borderRadius: 96,
  boxShadow: "0 24px 60px rgba(0,0,0,.42)",
  duration: 0.86,
  ease: fast,
}, 18.42);

// 8.1-14.9s: real evidence exists, but remains scattered around the speaker.
tl.set(".evidence, .scatter-label", { autoAlpha: 0 }, 0);
reveal(".evidence-voice", 8.25, { x: -150, y: -45, rotateZ: -10 }, {
  x: 0,
  y: 0,
  rotateZ: -4,
  duration: 0.55,
});
reveal(".evidence-file", 9.1, { x: 150, y: -55, rotateZ: 10 }, {
  x: 0,
  y: 0,
  rotateZ: 3,
  duration: 0.55,
});
reveal(".evidence-chat", 10.05, { x: 145, y: 90, rotateZ: 5 }, {
  x: 0,
  y: 0,
  rotateZ: -3,
  duration: 0.55,
});
reveal(".scatter-label", 11.16, { x: -78, y: 22 }, { x: 0, y: 0, duration: 0.52 });
tl.to(".evidence-voice", { y: -9, duration: 3.2, ease: "sine.inOut" }, 10.1);
tl.to(".evidence-file", { y: 8, duration: 3.4, ease: "sine.inOut" }, 10.3);
tl.to(".evidence-voice, .evidence-file", {
  autoAlpha: 0.16,
  scale: 0.9,
  duration: 0.24,
  ease: "power2.out",
}, 12.72);
tl.set(".evidence-chat", {
  x: -1700,
  y: -270,
  rotateZ: 0,
  scale: 1,
}, 12.72);
tl.to(".evidence-chat", {
  x: -1310,
  duration: 0.42,
  ease: fast,
}, 12.72);
tl.to(".scatter-label", { autoAlpha: 0, duration: 0.2 }, 12.72);

// 14.9-24.9s: handing off work still creates repeated explanation.
tl.set(".handoff, .repeat-ticket, .repeat-result", { autoAlpha: 0 }, 0);
reveal(".handoff", 15.08, { x: -80 }, { x: 0, duration: 0.46 });
reveal(".ticket-one", 16.0, { x: 135, rotateY: -10 }, { x: 0, rotateY: 0, duration: 0.42 });
reveal(".ticket-two", 17.0, { x: 135, rotateY: -10 }, { x: 0, rotateY: 0, duration: 0.42 });
reveal(".ticket-three", 18.1, { x: 135, rotateY: -10 }, { x: 0, rotateY: 0, duration: 0.42 });
tl.to(".repeat-ticket", { x: -16, duration: 0.18, stagger: 0.05, ease: settle }, 20.55);
reveal(".repeat-result", 21.05, { y: 62, scale: 0.92 }, { y: 0, scale: 1, duration: 0.54 });

// The recurring black contour establishes chapter changes without replaying A-roll.
tl.fromTo("#transition-diagnosis", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.12 }, 24.28);
tl.fromTo("#transition-diagnosis img", { scale: 1.02, x: 0, y: 0 }, {
  scale: 1.09,
  x: -34,
  y: 18,
  duration: 1.42,
  ease: "sine.inOut",
}, 24.28);
tl.fromTo("#transition-diagnosis > div", { autoAlpha: 0, y: 50 }, {
  autoAlpha: 1,
  y: 0,
  duration: 0.42,
  ease: fast,
}, 24.43);

// 24.9-33.5s: diagnose the actual bottleneck, then state the operating principle.
tl.set(".wrong-diagnosis, .right-diagnosis, .rule-rail, .rule-copy", { autoAlpha: 0 }, 0);
reveal(".wrong-diagnosis", 25.0, { x: -80 }, { x: 0, duration: 0.4 });
tl.fromTo(".wrong-diagnosis i", { scaleX: 0 }, { scaleX: 1, duration: 0.38, ease: "power3.out" }, 25.72);
hide(".wrong-diagnosis", 26.08, { x: -30 });
reveal(".right-diagnosis", 26.12, { y: 65, scale: 0.9 }, { y: 0, scale: 1, duration: 0.5 });
reveal(".rule-rail", 28.2, { x: 125, rotateY: -9 }, { x: 0, rotateY: 0, duration: 0.52 });
tl.fromTo(".rule-count", { scale: 0.65 }, {
  scale: 1,
  duration: 0.32,
  stagger: 0.18,
  ease: "back.out(1.45)",
}, 28.55);
reveal(".rule-copy", 29.48, { y: 55 }, { y: 0, duration: 0.45 });

// The principle is backed by the real Offer Doc, not a simulated document.
tl.fromTo("#offer-cover-broll", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.16 }, 29.22);
tl.fromTo("#offer-cover-broll .document-copy", { autoAlpha: 0, x: -90 }, {
  autoAlpha: 1,
  x: 0,
  duration: 0.52,
  ease: fast,
}, 29.4);
tl.fromTo("#offer-cover-broll img", { autoAlpha: 0, x: 90, rotateZ: 5, scale: 0.93 }, {
  autoAlpha: 1,
  x: 0,
  rotateZ: 2.5,
  scale: 1,
  duration: 0.62,
  ease: fast,
}, 29.38);
tl.to("#offer-cover-broll img", { scale: 1.035, duration: 3.05, ease: "sine.inOut", overwrite: "auto" }, 30.02);

// Pixel resolution marks the semantic change from fragments to a living memory.
tl.fromTo("#transition-memory", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.1 }, 33.05);
tl.fromTo("#transition-memory .pixel-field i", { autoAlpha: 0, scale: 0.15 }, {
  autoAlpha: 0.92,
  scale: 1,
  duration: 0.24,
  stagger: { each: 0.002, from: "random" },
  ease: "power3.out",
}, 33.05);
tl.fromTo("#transition-memory > div:last-child", { autoAlpha: 0, scale: 0.9 }, {
  autoAlpha: 1,
  scale: 1,
  duration: 0.38,
  ease: fast,
}, 33.28);
tl.to("#transition-memory .pixel-field", { autoAlpha: 0.18, duration: 0.32 }, 33.72);

tl.fromTo("#action-loop-broll img", { scale: 1.02, rotateY: -2.5 }, {
  scale: 1.08,
  rotateY: 0,
  duration: 3.26,
  ease: "power2.out",
}, 34.36);
reveal("#action-loop-broll .source-chip", 34.52, { x: -60 }, { x: 0, duration: 0.4 });

// 33.5-43.5s: reject random generation and assemble a continuously updated memory.
tl.set(".memory-denial, .memory-panel, .memory-title, .memory-spine, .memory-source, .memory-index", { autoAlpha: 0 }, 0);
reveal(".memory-denial", 33.68, { x: -75 }, { x: 0, duration: 0.4 });
hide(".memory-denial", 36.5, { x: -40 });
reveal(".memory-panel", 37.18, { x: 165, rotateY: -10 }, { x: 0, rotateY: 0, duration: 0.58 });
reveal(".memory-title", 37.46, { y: 40 }, { y: 0, duration: 0.42 });
reveal(".memory-spine", 37.78, { scaleY: 0, transformOrigin: "50% 0%" }, {
  scaleY: 1,
  duration: 0.58,
});
reveal(".source-voice", 38.05, { x: 100 }, { x: 0, duration: 0.44 });
reveal(".source-product", 38.78, { x: 100 }, { x: 0, duration: 0.44 });
reveal(".source-client", 39.5, { x: 100 }, { x: 0, duration: 0.44 });
reveal(".memory-index", 40.4, { y: 24 }, { y: 0, duration: 0.36 });

// 43.5-51.4s: one idea retrieves context and becomes a document, then an edit.
tl.set(".idea-chip, .retrieve-panel, .retrieve-focus, .retrieve-item, .output-doc, .output-arrow, .output-edit", { autoAlpha: 0 }, 0);
reveal(".idea-chip", 43.7, { x: -90 }, { x: 0, duration: 0.42 });
reveal(".retrieve-panel", 44.25, { x: -120, rotateY: 8 }, { x: 0, rotateY: 0, duration: 0.52 });
reveal(".retrieve-focus", 44.48, { y: 20 }, { y: 0, duration: 0.3 });
gsap.utils.toArray(".retrieve-item").forEach((node, index) => {
  reveal(node, 44.8 + index * 0.5, { x: -45 }, { x: 0, duration: 0.36 });
});
reveal(".output-doc", 46.65, { y: 95, rotateZ: -10, scale: 0.82 }, {
  y: 0,
  rotateZ: -3,
  scale: 1,
  duration: 0.5,
});
reveal(".output-arrow", 47.3, { x: -25 }, { x: 0, duration: 0.3 });
reveal(".output-edit", 47.68, { y: 95, rotateZ: 11, scale: 0.82 }, {
  y: 0,
  rotateZ: 3,
  scale: 1,
  duration: 0.5,
});

// The real editing timeline enters only when the narration reaches "进入剪辑".
tl.set("#editing-timeline-broll", {
  x: 0,
  y: 0,
  borderRadius: 0,
  scale: 1,
}, 49.80);
tl.fromTo("#editing-timeline-broll", { scale: 1.045 }, {
  scale: 1,
  duration: 1.58,
  ease: "power2.out",
}, 49.80);
tl.fromTo("#editing-broll-label", { autoAlpha: 0, x: 70 }, {
  autoAlpha: 1,
  x: 0,
  duration: 0.3,
  ease: fast,
}, 49.88);

// 51.4-54.9s: keep human responsibility explicit.
tl.set(".decision, .decision-note", { autoAlpha: 0 }, 0);
reveal(".decision-left", 51.55, { x: -125, rotateY: 10 }, { x: 0, rotateY: 0, duration: 0.48 });
reveal(".decision-right", 52.08, { x: 125, rotateY: -10 }, { x: 0, rotateY: 0, duration: 0.48 });
reveal(".decision-note", 52.62, { y: 40 }, { y: 0, duration: 0.4 });

// 54.9-61.5s: expressions accumulate into reusable assets.
tl.set(".asset-title, .asset-stack article", { autoAlpha: 0 }, 0);
reveal(".asset-title", 55.1, { x: -82 }, { x: 0, duration: 0.46 });
gsap.utils.toArray(".asset-stack article").forEach((node, index) => {
  reveal(node, 55.7 + index * 0.62, { x: 160, y: 80, rotateY: -20, scale: 0.8 }, {
    x: 0,
    y: 0,
    rotateY: index === 1 ? -5 : -7,
    scale: 1,
    duration: 0.58,
  });
});

tl.fromTo("#offer-loop-broll .document-copy", { autoAlpha: 0, x: 95 }, {
  autoAlpha: 1,
  x: 0,
  duration: 0.5,
  ease: fast,
}, 55.3);
tl.fromTo("#offer-loop-broll img", { autoAlpha: 0, x: -85, rotateZ: -5, scale: 0.94 }, {
  autoAlpha: 1,
  x: 0,
  rotateZ: -2.5,
  scale: 1,
  duration: 0.62,
  ease: fast,
}, 55.28);

// 61.5-64.1s: the third repetition is visibly cancelled.
tl.set(".count, .third-copy", { autoAlpha: 0 }, 0);
tl.fromTo(".count", { autoAlpha: 0, y: 80, scale: 0.72 }, {
  autoAlpha: 1,
  y: 0,
  scale: 1,
  duration: 0.34,
  stagger: 0.16,
  ease: fast,
}, 61.6);
tl.fromTo(".count-three i", { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: "power3.out" }, 62.18);
reveal(".third-copy", 62.22, { y: 45 }, { y: 0, duration: 0.42 });

tl.fromTo("#transition-brand", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.12 }, 63.72);
tl.fromTo("#transition-brand img", { scale: 1.04, x: 20, y: -12 }, {
  scale: 1.1,
  x: -28,
  y: 16,
  duration: 1.46,
  ease: "sine.inOut",
}, 63.72);
tl.fromTo("#transition-brand > div", { autoAlpha: 0, y: 42 }, {
  autoAlpha: 1,
  y: 0,
  duration: 0.4,
  ease: fast,
}, 63.88);

// 64.1-69.9s: brand promise stays operational, not abstract.
tl.set(".brand-lock, .brand-step", { autoAlpha: 0 }, 0);
reveal(".brand-lock", 64.28, { x: -90 }, { x: 0, duration: 0.48 });
gsap.utils.toArray(".brand-step").forEach((node, index) => {
  reveal(node, 64.62 + index * 0.7, { x: 130, rotateY: -9 }, {
    x: 0,
    rotateY: 0,
    duration: 0.46,
  });
});

// 69.9-80s: three real prior-video frames occupy the whole canvas before restoring to the speaker.
tl.set(".history-montage figure, .history-montage > div, .cta-message, .diagnosis, .cta-brand", { autoAlpha: 0 }, 0);
gsap.utils.toArray(".history-montage figure").forEach((node, index) => {
  reveal(node, 70.02 + index * 0.18, { y: 130, rotateY: index === 0 ? 24 : -20, scale: 0.76 }, {
    y: 0,
    scale: 1,
    duration: 0.52,
  });
});
reveal(".history-montage > div", 70.72, { y: 55 }, { y: 0, duration: 0.46 });
tl.to("#history-montage", { scale: 0.92, autoAlpha: 0, duration: 0.58, ease: fast }, 73.22);
reveal(".cta-message", 73.28, { x: 150, rotateY: -8 }, { x: 0, rotateY: 0, duration: 0.52 });
reveal(".diagnosis", 74.18, { y: 45 }, { y: 0, duration: 0.42 });
reveal(".cta-brand", 76.0, { y: 28 }, { y: 0, duration: 0.4 });

// Body captions gently settle in; the first three seconds intentionally have none.
document.querySelectorAll(".body-caption").forEach((caption) => {
  const start = Number(caption.dataset.start || 0);
  tl.fromTo(caption, { y: 18 }, { y: 0, duration: 0.18, ease: settle }, start);
});

window.__timelines["0813-yujun-boss-content-memory"] = tl;
