(function attachContourFlowBridge(global) {
  const api = global.HFNativeTransitions = global.HFNativeTransitions || {};

  function random(seed) {
    let state = seed >>> 0;
    return function next() {
      state = (state * 1664525 + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }

  function scalarField(config, time = 0) {
    const { columns, rows, seed, hillCount } = config.field;
    const next = random(seed);
    const hills = Array.from({ length: hillCount }, () => ({
      x: (next() * 1.18 - .09) * columns,
      y: (next() * 1.18 - .09) * rows,
      sx: columns * (.1 + next() * .16),
      sy: rows * (.12 + next() * .2),
      amplitude: .7 + next() * .65,
      phase: next() * Math.PI * 2
    }));
    const values = [];
    let minimum = Infinity;
    let maximum = -Infinity;
    for (let y = 0; y < rows; y += 1) {
      for (let x = 0; x < columns; x += 1) {
        let value = .06 * Math.sin(x * .39 + y * .17 + time * Math.PI * 1.2)
          + .04 * Math.cos(y * .52 - x * .11 - time * Math.PI);
        hills.forEach((hill) => {
          const driftX = Math.sin(hill.phase + time * Math.PI * 2) * columns * .045;
          const driftY = Math.cos(hill.phase * .8 + time * Math.PI * 1.7) * rows * .04;
          const dx = (x - hill.x - driftX) / hill.sx;
          const dy = (y - hill.y - driftY) / hill.sy;
          const breath = 1 + Math.sin(hill.phase + time * Math.PI * 2) * .08;
          value += hill.amplitude * breath * Math.exp(-.5 * (dx * dx + dy * dy));
        });
        values.push(value);
        minimum = Math.min(minimum, value);
        maximum = Math.max(maximum, value);
      }
    }
    const span = Math.max(.0001, maximum - minimum);
    return values.map((value) => (value - minimum) / span);
  }

  function renderContours(scene, config, time) {
    const layer = scene && scene.querySelector(".contour-lines");
    if (!layer) return;
    if (!global.d3 || !global.d3.contours || !global.d3.geoPath) {
      throw new Error("Contour Flow Bridge requires the pinned D3 bundle.");
    }
    const { columns, rows, thresholds } = config.field;
    const geometries = global.d3.contours()
      .size([columns, rows])
      .smooth(true)
      .thresholds(thresholds)(scalarField(config, time));
    const projection = global.d3.geoIdentity().scale(1920 / columns);
    const pathData = global.d3.geoPath(projection);
    geometries.forEach((geometry, index) => {
      let path = layer.children[index];
      if (!path) {
        path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "contour-line");
        layer.appendChild(path);
      }
      path.setAttribute("d", pathData(geometry));
    });
  }

  api.buildContours = function buildContours(root, config) {
    const scene = document.querySelector(root);
    if (!scene || scene.querySelector(".contour-lines")?.children.length) return;
    renderContours(scene, config, 0);
  };

  api.prepareContours = function prepareContours(root) {
    document.querySelectorAll(`${root} .contour-line`).forEach((path) => {
      const length = path.getTotalLength();
      path.style.strokeDasharray = String(length);
      path.style.strokeDashoffset = String(length);
    });
  };

  api.animateContours = function animateContours(timeline, root, at, config) {
    const scene = document.querySelector(root);
    const fieldState = { time: 0 };
    timeline.to(fieldState, {
      time: 1,
      duration: config.motion.evolveSeconds || 1.2,
      ease: "none",
      onUpdate: () => renderContours(scene, config, fieldState.time)
    }, at);
    timeline.to(`${root} .contour-line`, {
      strokeDashoffset: 0,
      duration: config.motion.drawSeconds,
      stagger: config.motion.lineStaggerSeconds,
      ease: "power2.out"
    }, at);
    timeline.fromTo(`${root} .transition-copy`, { y: 70, opacity: 0 }, {
      y: 0,
      opacity: 1,
      duration: config.motion.copyRevealSeconds
    }, at + 0.34);
    timeline.fromTo(`${root} .contour-accent`, { scale: 0, opacity: 0 }, {
      scale: 1,
      opacity: 1,
      duration: 0.22,
      ease: "back.out(1.4)"
    }, at + 0.48);
  };
})(window);
