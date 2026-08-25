(function attachPixelResolveBridge(global) {
  const api = global.HFNativeTransitions = global.HFNativeTransitions || {};

  api.buildPixelGrid = function buildPixelGrid(root, config) {
    const scene = document.querySelector(root);
    const grid = scene.querySelector(".pixel-grid");
    if (!grid || grid.children.length) return;
    const columns = config.grid.columns;
    const rows = config.grid.rows;
    grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
    grid.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
    grid.style.gap = `${config.grid.gapPixels}px`;
    for (let index = 0; index < columns * rows; index += 1) {
      const cell = document.createElement("span");
      cell.className = "pixel-cell";
      grid.appendChild(cell);
    }
  };

  api.animatePixelResolve = function animatePixelResolve(timeline, root, at, config) {
    const gridShape = [config.grid.rows, config.grid.columns];
    timeline.fromTo(`${root} .pixel-source`, { opacity: 0 }, {
      opacity: 1,
      duration: config.motion.sourceFreezeSeconds,
      ease: "steps(2)"
    }, at);
    timeline.fromTo(`${root} .pixel-cell`, { scale: 0, opacity: 0 }, {
      scale: 1,
      opacity: 1,
      duration: config.motion.coverSeconds,
      stagger: { amount: 0.24, grid: gridShape, from: "edges" },
      ease: "steps(4)"
    }, at + .12);
    timeline.fromTo(`${root} .transition-copy`, { opacity: 0 }, {
      opacity: 1,
      duration: config.motion.copyRevealSeconds,
      ease: "steps(3)"
    }, at + .38);
    timeline.to(`${root} .pixel-source`, {
      opacity: 0,
      duration: .08,
      ease: "steps(2)"
    }, at + .48);
    timeline.to(`${root} .pixel-cell`, {
      scale: 0,
      opacity: 0,
      duration: config.motion.resolveSeconds,
      stagger: { amount: 0.2, grid: gridShape, from: "center" },
      ease: "steps(5)"
    }, at + .5);
  };
})(window);
