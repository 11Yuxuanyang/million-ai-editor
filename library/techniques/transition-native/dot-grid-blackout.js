(function attachDotGridBlackout(global) {
  const api = global.HFNativeTransitions = global.HFNativeTransitions || {};
  const SVG_NS = "http://www.w3.org/2000/svg";

  function random(seed) {
    let state = seed >>> 0;
    return function next() {
      state = (state * 1664525 + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }

  function makeSvgNode(tag, className) {
    const node = document.createElementNS(SVG_NS, tag);
    if (className) node.setAttribute("class", className);
    return node;
  }

  function buildNetwork(groups, config, bounds) {
    const next = random(config.seed || 703);
    const columns = config.grid.columns;
    const rows = config.grid.rows;
    const xStep = bounds.width / columns;
    const yStep = bounds.height / rows;
    const nodes = Array.from({ length: rows }, () => Array(columns).fill(null));
    const skipChance = config.grid.skipChance ?? .28;

    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        if (next() < skipChance) continue;
        const jitterX = (next() - .5) * xStep * config.grid.jitterRatio;
        const jitterY = (next() - .5) * yStep * config.grid.jitterRatio;
        const point = {
          x: (column + .5) * xStep + jitterX,
          y: (row + .5) * yStep + jitterY
        };
        nodes[row][column] = point;

        const dot = makeSvgNode("circle", groups.pointClass);
        dot.setAttribute("cx", String(point.x));
        dot.setAttribute("cy", String(point.y));
        dot.setAttribute("r", String(1.2 + next() * 1.5));
        groups.points.appendChild(dot);
      }
    }

    const horizontalChance = config.connections?.horizontalChance ?? .18;
    const verticalChance = config.connections?.verticalChance ?? .08;
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const point = nodes[row][column];
        if (!point) continue;
        const candidates = [
          { point: nodes[row]?.[column + 1], chance: horizontalChance },
          { point: nodes[row + 1]?.[column], chance: verticalChance }
        ];
        candidates.forEach((candidate) => {
          if (!candidate.point || next() > candidate.chance) return;
          const line = makeSvgNode("line", groups.linkClass);
          line.setAttribute("x1", String(point.x));
          line.setAttribute("y1", String(point.y));
          line.setAttribute("x2", String(candidate.point.x));
          line.setAttribute("y2", String(candidate.point.y));
          groups.links.appendChild(line);
        });
      }
    }
  }

  api.buildDotGrid = function buildDotGrid(root, config) {
    const scene = document.querySelector(root);
    const points = scene?.querySelector(".dot-points");
    const links = scene?.querySelector(".dot-links");
    if (!scene || !points || !links || points.children.length) return;
    buildNetwork(
      { points, links, pointClass: "dot-point", linkClass: "dot-link" },
      config,
      { width: 1920, height: 1080 }
    );
  };

  api.animateDotGridBlackout = function animateDotGridBlackout(timeline, root, at, config) {
    timeline.fromTo(`${root} .dot-network`, { x: -14, y: 9 }, {
      x: 16,
      y: -10,
      duration: config.motion.driftSeconds || 1.05,
      ease: "sine.inOut"
    }, at);
    timeline.fromTo(`${root} .dot-link`, { opacity: 0 }, {
      opacity: .28,
      duration: config.motion.lineRevealSeconds || .42,
      stagger: { amount: .18, from: "random" },
      ease: "power1.out"
    }, at);
    timeline.fromTo(`${root} .dot-point`, { opacity: 0, scale: .6 }, {
      opacity: 0.46,
      scale: 1,
      duration: config.motion.pointRevealSeconds,
      stagger: { amount: .28, from: "random" },
      ease: "power1.out"
    }, at);
    timeline.to(`${root} .dot-point:nth-child(4n)`, {
      opacity: .18,
      scale: .78,
      duration: .34,
      yoyo: true,
      repeat: 1,
      ease: "sine.inOut"
    }, at + .35);
    timeline.fromTo(`${root} .transition-copy`, { y: 32, opacity: 0 }, {
      y: 0,
      opacity: 1,
      duration: config.motion.copyRevealSeconds,
      ease: "power3.out"
    }, at + .36);
  };

  api.buildAmbientNetwork = function buildAmbientNetwork(root, config) {
    const scene = document.querySelector(root);
    if (!scene || scene.querySelector(".ambient-network-field")) return;
    const svg = makeSvgNode("svg", "ambient-network-field");
    svg.setAttribute("viewBox", "0 0 1920 1080");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("data-layout-allow-overflow", "");
    const network = makeSvgNode("g", "ambient-network");
    network.setAttribute("data-layout-allow-overflow", "");
    const links = makeSvgNode("g", "ambient-links");
    const points = makeSvgNode("g", "ambient-points");
    network.appendChild(links);
    network.appendChild(points);
    svg.appendChild(network);
    const first = scene.firstElementChild;
    const hasGround = first?.classList.contains("dark-fill") || first?.classList.contains("blue-fill");
    scene.insertBefore(svg, hasGround ? first.nextSibling : first);
    buildNetwork(
      { points, links, pointClass: "ambient-point", linkClass: "ambient-link" },
      config,
      { width: 1920, height: 1080 }
    );
  };

  api.animateAmbientNetwork = function animateAmbientNetwork(timeline, root, at, duration) {
    timeline.fromTo(`${root} .ambient-network`, { x: -22, y: 12 }, {
      x: 26,
      y: -14,
      duration,
      ease: "sine.inOut"
    }, at);
    timeline.fromTo(`${root} .ambient-link`, { opacity: 0 }, {
      opacity: .2,
      duration: .72,
      stagger: { amount: .3, from: "random" },
      ease: "power1.out"
    }, at);
    timeline.fromTo(`${root} .ambient-point`, { opacity: 0, scale: .72 }, {
      opacity: .42,
      scale: 1,
      duration: .55,
      stagger: { amount: .38, from: "random" },
      ease: "power1.out"
    }, at + .08);
    timeline.to(`${root} .ambient-point:nth-child(3n)`, {
      opacity: .16,
      scale: .82,
      duration: .8,
      repeat: Math.max(1, Math.floor(duration / 1.6)),
      yoyo: true,
      ease: "sine.inOut"
    }, at + .45);
  };
})(window);
