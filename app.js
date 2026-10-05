"use strict";

let COLORS = {};

const elements = {
  omegaM: document.querySelector("#omega-m"),
  omegaMOutput: document.querySelector("#omega-m-output"),
  h0: document.querySelector("#h0"),
  h0Output: document.querySelector("#h0-output"),
  scatter: document.querySelector("#intrinsic-scatter"),
  scatterOutput: document.querySelector("#intrinsic-scatter-output"),
  profileOffset: document.querySelector("#profile-offset"),
  manualOffset: document.querySelector("#magnitude-offset"),
  manualOffsetOutput: document.querySelector("#magnitude-offset-output"),
  offsetControl: document.querySelector("#offset-control"),
  zMin: document.querySelector("#redshift-cut"),
  axisScale: document.querySelector("#axis-scale"),
  status: document.querySelector("#analysis-status"),
  hubble: document.querySelector("#hubble-chart"),
  residual: document.querySelector("#residual-chart"),
  profile: document.querySelector("#profile-chart"),
  tooltip: document.querySelector("#chart-tooltip"),
  interpretation: document.querySelector("#interpretation-copy"),
  table: document.querySelector("#data-table-body"),
  download: document.querySelector("#download-csv"),
  themeToggle: document.querySelector("#theme-toggle"),
  carousel: document.querySelector("#observation-carousel"),
  carouselPrevious: document.querySelector("#carousel-previous"),
  carouselPlay: document.querySelector("#carousel-play"),
  carouselNext: document.querySelector("#carousel-next"),
  carouselSlides: [...document.querySelectorAll(".observation-slide")],
  carouselDots: [...document.querySelectorAll(".carousel-dots button")],
  carouselIndex: document.querySelector("#carousel-index"),
  carouselStatus: document.querySelector("#carousel-status")
};

const worker = new Worker("physicsWorker.js");
let reference = null;
let analysis = null;
let latestRunId = 0;
let runTimer = null;
let hitPoints = [];
let currentSlide = 0;
let carouselTimer = null;
let carouselSuspended = false;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let carouselUserPaused = reducedMotion.matches;

const presets = {
  fiducial: { omegaM: 0.3, h0: 70, scatter: 0.1, zMin: 0.01 },
  pantheon: { omegaM: 0.334, h0: 70, scatter: 0.1, zMin: 0.01 },
  matter: { omegaM: 1, h0: 70, scatter: 0.1, zMin: 0.01 }
};

function syncCanvasColors() {
  const css = getComputedStyle(document.documentElement);
  COLORS = {
    ink: css.getPropertyValue("--ink").trim(),
    muted: css.getPropertyValue("--muted").trim(),
    faint: css.getPropertyValue("--faint").trim(),
    grid: css.getPropertyValue("--line").trim(),
    accent: css.getPropertyValue("--accent").trim(),
    accentSoft: css.getPropertyValue("--accent-soft").trim(),
    comparison: css.getPropertyValue("--comparison").trim(),
    point: css.getPropertyValue("--point").trim(),
    excluded: css.getPropertyValue("--faint").trim(),
    danger: css.getPropertyValue("--danger").trim(),
    band: css.getPropertyValue("--canvas-band").trim()
  };
}

function setTheme(theme, persist = true) {
  document.documentElement.dataset.theme = theme;
  if (persist) localStorage.setItem("sn-theme", theme);
  const isDark = theme === "dark";
  elements.themeToggle.setAttribute("aria-pressed", String(isDark));
  elements.themeToggle.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
  syncCanvasColors();
  requestAnimationFrame(drawAll);
}

function showSlide(index, announce = false) {
  currentSlide = (index + elements.carouselSlides.length) % elements.carouselSlides.length;
  elements.carouselSlides.forEach((slide, slideIndex) => {
    const active = slideIndex === currentSlide;
    slide.classList.toggle("is-active", active);
    slide.setAttribute("aria-hidden", String(!active));
  });
  elements.carouselDots.forEach((dot, dotIndex) => {
    const active = dotIndex === currentSlide;
    dot.classList.toggle("is-active", active);
    dot.setAttribute("aria-pressed", String(active));
  });
  elements.carouselIndex.textContent = String(currentSlide + 1).padStart(2, "0");
  if (announce) {
    const title = elements.carouselSlides[currentSlide].querySelector("h2").textContent;
    elements.carouselStatus.textContent = `Showing observation ${currentSlide + 1} of ${elements.carouselSlides.length}: ${title}`;
  }
}

function restartCarousel() {
  clearInterval(carouselTimer);
  if (!carouselUserPaused && !carouselSuspended && !reducedMotion.matches) {
    carouselTimer = setInterval(() => showSlide(currentSlide + 1), 7000);
  }
}

function syncCarouselPauseButton() {
  const paused = carouselUserPaused || reducedMotion.matches;
  elements.carouselPlay.classList.toggle("is-paused", paused);
  elements.carouselPlay.setAttribute("aria-pressed", String(paused));
  elements.carouselPlay.setAttribute("aria-label", paused ? "Play slideshow" : "Pause slideshow");
}

function bindCarousel() {
  const navigate = (offset) => {
    showSlide(currentSlide + offset, true);
    restartCarousel();
  };
  elements.carouselPrevious.addEventListener("click", () => navigate(-1));
  elements.carouselNext.addEventListener("click", () => navigate(1));
  elements.carouselDots.forEach((dot, index) => dot.addEventListener("click", () => {
    showSlide(index, true);
    restartCarousel();
  }));
  elements.carouselPlay.addEventListener("click", () => {
    carouselUserPaused = !carouselUserPaused;
    syncCarouselPauseButton();
    restartCarousel();
  });
  elements.carousel.addEventListener("mouseenter", () => { carouselSuspended = true; restartCarousel(); });
  elements.carousel.addEventListener("mouseleave", () => { carouselSuspended = false; restartCarousel(); });
  elements.carousel.addEventListener("focusin", () => { carouselSuspended = true; restartCarousel(); });
  elements.carousel.addEventListener("focusout", (event) => {
    if (!elements.carousel.contains(event.relatedTarget)) { carouselSuspended = false; restartCarousel(); }
  });
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) carouselUserPaused = true;
    syncCarouselPauseButton();
    restartCarousel();
  });
  showSlide(0);
  syncCarouselPauseButton();
  restartCarousel();
}

function currentParams() {
  return {
    omegaM: Number(elements.omegaM.value),
    h0: Number(elements.h0.value),
    intrinsicScatter: Number(elements.scatter.value),
    profileOffset: elements.profileOffset.checked,
    manualOffset: Number(elements.manualOffset.value),
    zMin: Number(elements.zMin.value)
  };
}

function syncOutputs() {
  elements.omegaMOutput.value = Number(elements.omegaM.value).toFixed(3);
  elements.h0Output.value = `${Number(elements.h0.value).toFixed(1)} km s⁻¹ Mpc⁻¹`;
  elements.scatterOutput.value = `${Number(elements.scatter.value).toFixed(2)} mag`;
  elements.manualOffsetOutput.value = `${Number(elements.manualOffset.value).toFixed(3)} mag`;
  elements.manualOffset.disabled = elements.profileOffset.checked;
  elements.offsetControl.setAttribute("aria-disabled", String(elements.profileOffset.checked));
}

function setStatus(text, mode) {
  elements.status.className = `analysis-status ${mode ? `is-${mode}` : ""}`.trim();
  elements.status.querySelector("span:last-child").textContent = text;
}

function scheduleAnalysis() {
  syncOutputs();
  document.querySelectorAll(".preset").forEach((button) => button.classList.remove("is-active"));
  clearTimeout(runTimer);
  setStatus("Recomputing likelihood", "working");
  runTimer = setTimeout(runAnalysis, 90);
}

function runAnalysis() {
  if (!reference) return;
  latestRunId += 1;
  worker.postMessage({ runId: latestRunId, points: reference.points, params: currentParams() });
  updateUrl();
}

function updateUrl() {
  const params = currentParams();
  const url = new URL(window.location.href);
  url.searchParams.set("om", params.omegaM.toFixed(3));
  url.searchParams.set("h0", params.h0.toFixed(1));
  url.searchParams.set("scatter", params.intrinsicScatter.toFixed(3));
  url.searchParams.set("zmin", params.zMin.toFixed(3));
  url.searchParams.set("offset", params.profileOffset ? "profile" : params.manualOffset.toFixed(3));
  url.searchParams.set("axis", elements.axisScale.value);
  url.searchParams.delete("v");
  history.replaceState(null, "", url);
}

function loadUrlState() {
  const params = new URLSearchParams(window.location.search);
  const assignNumber = (key, element) => {
    if (!params.has(key)) return;
    const value = Number(params.get(key));
    if (Number.isFinite(value) && value >= Number(element.min || -Infinity) && value <= Number(element.max || Infinity)) element.value = String(value);
  };
  assignNumber("om", elements.omegaM);
  assignNumber("h0", elements.h0);
  assignNumber("scatter", elements.scatter);
  if (["0.001", "0.010", "0.023"].includes(Number(params.get("zmin")).toFixed(3))) elements.zMin.value = String(Number(params.get("zmin")));
  const offset = params.get("offset");
  if (offset && offset !== "profile" && Number.isFinite(Number(offset))) {
    elements.profileOffset.checked = false;
    elements.manualOffset.value = offset;
  }
  if (["log", "linear"].includes(params.get("axis"))) elements.axisScale.value = params.get("axis");
  syncOutputs();
}

function bindControls() {
  elements.themeToggle.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
  [elements.omegaM, elements.h0, elements.scatter, elements.manualOffset].forEach((input) => input.addEventListener("input", scheduleAnalysis));
  [elements.profileOffset, elements.zMin].forEach((input) => input.addEventListener("change", scheduleAnalysis));
  elements.axisScale.addEventListener("change", () => { updateUrl(); drawAll(); });
  document.querySelectorAll(".preset").forEach((button) => button.addEventListener("click", () => {
    const preset = presets[button.dataset.preset];
    elements.omegaM.value = String(preset.omegaM);
    elements.h0.value = String(preset.h0);
    elements.scatter.value = String(preset.scatter);
    elements.zMin.value = String(preset.zMin);
    elements.profileOffset.checked = true;
    document.querySelectorAll(".preset").forEach((candidate) => candidate.classList.toggle("is-active", candidate === button));
    syncOutputs();
    setStatus("Recomputing likelihood", "working");
    clearTimeout(runTimer);
    runTimer = setTimeout(runAnalysis, 40);
  }));
  elements.download.addEventListener("click", downloadResiduals);
  elements.hubble.addEventListener("pointermove", showTooltip);
  elements.hubble.addEventListener("pointerleave", () => { elements.tooltip.hidden = true; });
}

function canvasContext(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(rect.width * ratio));
  const height = Math.max(1, Math.round(rect.height * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, rect.width, rect.height);
  context.lineCap = "round";
  context.lineJoin = "round";
  return { context, width: rect.width, height: rect.height };
}

function redshiftTransform(minimum, maximum) {
  if (elements.axisScale.value === "log") {
    const low = Math.log10(minimum);
    const high = Math.log10(maximum);
    return (value) => (Math.log10(value) - low) / (high - low);
  }
  return (value) => (value - minimum) / (maximum - minimum);
}

function drawFrame(context, width, height, options = {}) {
  const margin = { left: 62, right: 22, top: 22, bottom: 48, ...options.margin };
  const plot = { left: margin.left, top: margin.top, right: width - margin.right, bottom: height - margin.bottom };
  context.strokeStyle = COLORS.grid;
  context.lineWidth = 1;
  context.strokeRect(plot.left, plot.top, plot.right - plot.left, plot.bottom - plot.top);
  return plot;
}

function drawText(context, text, x, y, align = "center", color = COLORS.muted, font = "10px IBM Plex Mono") {
  context.fillStyle = color;
  context.font = font;
  context.textAlign = align;
  context.textBaseline = "middle";
  context.fillText(text, x, y);
}

function drawHubble() {
  if (!analysis || !reference) return;
  const { context, width, height } = canvasContext(elements.hubble);
  const plot = drawFrame(context, width, height);
  const minimumX = Math.min(...reference.points.map((point) => point.x));
  const maximumX = Math.max(...reference.points.map((point) => point.x));
  const xUnit = redshiftTransform(minimumX, maximumX);
  const allY = [...reference.points.map((point) => point.y), ...analysis.model.map((point) => point.y), ...analysis.matterModel.map((point) => point.y)];
  const minimumY = Math.floor(Math.min(...allY) - 1);
  const maximumY = Math.ceil(Math.max(...allY) + 1);
  const x = (value) => plot.left + xUnit(value) * (plot.right - plot.left);
  const y = (value) => plot.bottom - (value - minimumY) / (maximumY - minimumY) * (plot.bottom - plot.top);

  const xTicks = elements.axisScale.value === "log" ? [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 2] : [0, 0.5, 1, 1.5, 2];
  xTicks.filter((tick) => tick >= minimumX && tick <= maximumX).forEach((tick) => {
    const px = x(tick);
    context.strokeStyle = COLORS.grid;
    context.beginPath(); context.moveTo(px, plot.top); context.lineTo(px, plot.bottom); context.stroke();
    drawText(context, tick < .01 ? tick.toFixed(3) : tick < .1 ? tick.toFixed(2) : String(tick), px, plot.bottom + 19);
  });
  const yStep = maximumY - minimumY > 16 ? 4 : 2;
  for (let tick = Math.ceil(minimumY / yStep) * yStep; tick <= maximumY; tick += yStep) {
    const py = y(tick);
    context.strokeStyle = COLORS.grid;
    context.beginPath(); context.moveTo(plot.left, py); context.lineTo(plot.right, py); context.stroke();
    drawText(context, String(tick), plot.left - 11, py, "right");
  }
  drawText(context, `Redshift z${elements.axisScale.value === "log" ? " (log scale)" : ""}`, (plot.left + plot.right) / 2, height - 13, "center", COLORS.muted, "11px DM Sans");
  context.save(); context.translate(15, (plot.top + plot.bottom) / 2); context.rotate(-Math.PI / 2); drawText(context, "Distance modulus μ (mag)", 0, 0, "center", COLORS.muted, "11px DM Sans"); context.restore();

  const line = (series, color, dashed = false) => {
    context.strokeStyle = color; context.lineWidth = 2; context.setLineDash(dashed ? [7, 6] : []); context.beginPath();
    series.forEach((point, index) => index ? context.lineTo(x(point.x), y(point.y)) : context.moveTo(x(point.x), y(point.y)));
    context.stroke(); context.setLineDash([]);
  };
  line(analysis.matterModel, COLORS.comparison, true);
  line(analysis.model, COLORS.accent, false);

  hitPoints = [];
  reference.points.forEach((point, index) => {
    const residual = analysis.residuals[index];
    const px = x(point.x); const py = y(point.y);
    const upper = y(point.y + point.y_err); const lower = y(point.y - point.y_err);
    context.globalAlpha = residual.included ? .78 : .2;
    context.strokeStyle = residual.included ? COLORS.point : COLORS.excluded;
    context.lineWidth = .8;
    context.beginPath(); context.moveTo(px, upper); context.lineTo(px, lower); context.moveTo(px - 2.5, upper); context.lineTo(px + 2.5, upper); context.moveTo(px - 2.5, lower); context.lineTo(px + 2.5, lower); context.stroke();
    context.fillStyle = residual.included ? COLORS.point : COLORS.excluded;
    context.beginPath(); context.arc(px, py, residual.included ? 2.3 : 1.7, 0, Math.PI * 2); context.fill();
    context.globalAlpha = 1;
    hitPoints.push({ x: px, y: py, point, residual });
  });
}

function drawResiduals() {
  if (!analysis || !reference) return;
  const { context, width, height } = canvasContext(elements.residual);
  const plot = drawFrame(context, width, height, { margin: { top: 15, bottom: 43 } });
  const minimumX = Math.min(...reference.points.map((point) => point.x));
  const maximumX = Math.max(...reference.points.map((point) => point.x));
  const xUnit = redshiftTransform(minimumX, maximumX);
  const includedAbsolute = analysis.residuals.filter((row) => row.included).map((row) => Math.abs(row.standardized)).sort((a, b) => a - b);
  const robustMaximum = includedAbsolute[Math.floor(includedAbsolute.length * .97)] || 3;
  const yMaximum = Math.min(8, Math.max(4, Math.ceil(robustMaximum + .5)));
  const x = (value) => plot.left + xUnit(value) * (plot.right - plot.left);
  const y = (value) => plot.bottom - (value + yMaximum) / (2 * yMaximum) * (plot.bottom - plot.top);
  context.fillStyle = COLORS.band; context.fillRect(plot.left, y(1), plot.right - plot.left, y(-1) - y(1));
  [-2, 0, 2].forEach((tick) => {
    context.strokeStyle = tick === 0 ? COLORS.faint : COLORS.grid;
    context.setLineDash(tick === 0 ? [] : [5, 5]);
    context.beginPath(); context.moveTo(plot.left, y(tick)); context.lineTo(plot.right, y(tick)); context.stroke(); context.setLineDash([]);
    drawText(context, tick === 0 ? "0" : `${tick > 0 ? "+" : ""}${tick}σ`, plot.left - 10, y(tick), "right");
  });
  analysis.residuals.forEach((row) => {
    const clipped = Math.max(-yMaximum, Math.min(yMaximum, row.standardized));
    context.globalAlpha = row.included ? .78 : .18;
    context.fillStyle = Math.abs(row.standardized) > 3 ? COLORS.danger : row.included ? COLORS.point : COLORS.excluded;
    context.beginPath(); context.arc(x(row.x), y(clipped), 2.2, 0, Math.PI * 2); context.fill(); context.globalAlpha = 1;
  });
  drawText(context, "Redshift z", (plot.left + plot.right) / 2, height - 12, "center", COLORS.muted, "11px DM Sans");
}

function drawProfile() {
  if (!analysis) return;
  const { context, width, height } = canvasContext(elements.profile);
  const plot = drawFrame(context, width, height);
  const maximumDelta = Math.min(25, Math.max(6, Math.ceil(Math.max(...analysis.profile.map((row) => Math.min(row.deltaChi2, 25))))));
  const x = (value) => plot.left + (value - .05) / .95 * (plot.right - plot.left);
  const y = (value) => plot.bottom - Math.min(value, maximumDelta) / maximumDelta * (plot.bottom - plot.top);

  context.fillStyle = COLORS.band;
  context.fillRect(x(.316), plot.top, x(.352) - x(.316), plot.bottom - plot.top);
  for (let tick = .2; tick <= 1.001; tick += .2) {
    const px = x(tick); context.strokeStyle = COLORS.grid; context.beginPath(); context.moveTo(px, plot.top); context.lineTo(px, plot.bottom); context.stroke(); drawText(context, tick.toFixed(1), px, plot.bottom + 19);
  }
  [0, 1, 4].forEach((tick) => {
    const py = y(tick); context.strokeStyle = tick === 0 ? COLORS.faint : COLORS.grid; context.setLineDash(tick ? [5, 5] : []); context.beginPath(); context.moveTo(plot.left, py); context.lineTo(plot.right, py); context.stroke(); context.setLineDash([]); drawText(context, String(tick), plot.left - 10, py, "right");
  });
  context.strokeStyle = COLORS.accent; context.lineWidth = 2; context.beginPath();
  analysis.profile.forEach((row, index) => index ? context.lineTo(x(row.omegaM), y(row.deltaChi2)) : context.moveTo(x(row.omegaM), y(row.deltaChi2)));
  context.stroke();
  const best = analysis.metrics.bestOmegaM;
  context.fillStyle = COLORS.accent; context.beginPath(); context.arc(x(best), y(0), 4, 0, Math.PI * 2); context.fill();
  context.strokeStyle = COLORS.comparison; context.setLineDash([3, 4]); context.beginPath(); context.moveTo(x(.334), plot.top); context.lineTo(x(.334), plot.bottom); context.stroke(); context.setLineDash([]);
  context.strokeStyle = COLORS.ink; context.setLineDash([2, 5]); context.beginPath(); context.moveTo(x(analysis.params.omegaM), plot.top); context.lineTo(x(analysis.params.omegaM), plot.bottom); context.stroke(); context.setLineDash([]);
  drawText(context, "Matter density Ωm", (plot.left + plot.right) / 2, height - 13, "center", COLORS.muted, "11px DM Sans");
  context.save(); context.translate(15, (plot.top + plot.bottom) / 2); context.rotate(-Math.PI / 2); drawText(context, "Δχ²", 0, 0, "center", COLORS.muted, "11px DM Sans"); context.restore();
  drawText(context, "Pantheon+ published benchmark", x(.334) + 7, plot.top + 12, "left", COLORS.comparison, "10px IBM Plex Mono");
}

function showTooltip(event) {
  if (!hitPoints.length) return;
  const rect = elements.hubble.getBoundingClientRect();
  const localX = event.clientX - rect.left;
  const localY = event.clientY - rect.top;
  let nearest = null; let distance = Infinity;
  for (const hit of hitPoints) {
    const candidate = Math.hypot(hit.x - localX, hit.y - localY);
    if (candidate < distance) { distance = candidate; nearest = hit; }
  }
  if (!nearest || distance > 14) { elements.tooltip.hidden = true; return; }
  elements.tooltip.replaceChildren();
  const title = document.createElement("strong"); title.textContent = nearest.point.label || "Pantheon+ light curve";
  const values = document.createElement("span"); values.textContent = `z = ${nearest.point.x.toFixed(5)}\nμ = ${nearest.point.y.toFixed(3)} ± ${nearest.point.y_err.toFixed(3)}\nresidual = ${nearest.residual.residual.toFixed(3)} mag\n${nearest.residual.included ? "included" : "below low-z cut"}`;
  elements.tooltip.append(title, values); elements.tooltip.hidden = false;
  const left = Math.min(rect.width - 175, Math.max(8, localX + 14));
  const top = Math.min(rect.height - 115, Math.max(8, localY - 20));
  elements.tooltip.style.left = `${left}px`; elements.tooltip.style.top = `${top}px`;
}

function updateMetrics() {
  const metrics = analysis.metrics;
  const outlierCount = analysis.residuals.filter((row) => row.included && Math.abs(row.standardized) > 3).length;
  document.querySelector("#metric-best-omega").textContent = metrics.bestOmegaM.toFixed(3);
  const low = metrics.intervalLow == null ? "boundary" : metrics.intervalLow.toFixed(3);
  const high = metrics.intervalHigh == null ? "boundary" : metrics.intervalHigh.toFixed(3);
  document.querySelector("#metric-interval").textContent = `Δχ² = 1 interval: ${low}–${high}`;
  document.querySelector("#metric-delta-chi").textContent = `Δχ² ${metrics.matterDeltaChi2.toFixed(1)}`;
  document.querySelector("#metric-current-chi").textContent = metrics.chi2PerDatum.toFixed(2);
  document.querySelector("#metric-offset").textContent = `${metrics.effectiveOffset >= 0 ? "+" : ""}${metrics.effectiveOffset.toFixed(3)} mag`;
  document.querySelector("#metric-q0").textContent = `${metrics.q0 >= 0 ? "+" : ""}${metrics.q0.toFixed(3)}`;
  document.querySelector("#metric-transition").textContent = metrics.transitionRedshift == null ? "no past acceleration transition" : `transition z ≈ ${metrics.transitionRedshift.toFixed(2)}`;
  document.querySelector("#hubble-description").textContent = `Observed distance moduli with diagonal uncertainty bars. The current flat ΛCDM curve uses Ωm ${analysis.params.omegaM.toFixed(3)} and offset ${metrics.effectiveOffset.toFixed(3)} magnitude; ${metrics.includedCount} light curves are included in the fit.`;
  document.querySelector("#residual-description").textContent = `Standardized observed-minus-model residuals for ${metrics.includedCount} included light curves. ${outlierCount} have absolute standardized residual greater than 3. The shaded band marks plus or minus 1 sigma and dashed lines mark plus or minus 2 sigma.`;
  document.querySelector("#profile-description").textContent = `The diagonal-error subset profile reaches its minimum at Ωm ${metrics.bestOmegaM.toFixed(3)}. The blue band marks the published Pantheon+ SNe-only benchmark Ωm 0.334 plus or minus 0.018 for context, not as a target fitted by this simplified analysis.`;

  const acceleration = metrics.q0 < 0
    ? `The selected Ω<sub>m</sub> gives <strong>q<sub>0</sub> = ${metrics.q0.toFixed(3)}</strong>, so this flat model is accelerating today.`
    : `The selected Ω<sub>m</sub> gives <strong>q<sub>0</sub> = ${metrics.q0.toFixed(3)}</strong>, so this flat model is not accelerating today.`;
  const intervalText = metrics.intervalLow == null || metrics.intervalHigh == null
    ? "The Δχ² = 1 profile reaches the grid boundary, so a closed interval is not available."
    : `Within this simplified likelihood, the profile minimum is <strong>Ω<sub>m</sub> = ${metrics.bestOmegaM.toFixed(3)}</strong> with a Δχ² = 1 interval of ${metrics.intervalLow.toFixed(3)}–${metrics.intervalHigh.toFixed(3)}.`;
  elements.interpretation.innerHTML = `<p>${acceleration}</p><p>${intervalText}</p><p>An offset-profiled Ω<sub>m</sub> = 1 curve is separated from the subset minimum by <strong>Δχ² = ${metrics.matterDeltaChi2.toFixed(1)}</strong>. This is a model-comparison diagnostic under diagonal independent errors—not a published detection significance.</p><p>The current cut includes <strong>${metrics.includedCount}</strong> of ${reference.points.length} bundled light curves; ${metrics.excludedCount} low-redshift entries remain visible but are excluded from χ².</p>`;
}

function updateTable() {
  const fragment = document.createDocumentFragment();
  analysis.residuals.forEach((row) => {
    const tr = document.createElement("tr");
    [row.label || "—", row.x.toFixed(5), row.observed.toFixed(4), row.error.toFixed(4), row.included ? "yes" : "no", row.residual.toFixed(4), row.standardized.toFixed(3)].forEach((value) => {
      const td = document.createElement("td"); td.textContent = value; tr.appendChild(td);
    });
    fragment.appendChild(tr);
  });
  elements.table.replaceChildren(fragment);
}

function downloadResiduals() {
  if (!analysis) return;
  const rows = ["object,zHD,mu_observed,sigma_diagonal,sigma_effective,included,residual_mag,standardized_residual"];
  analysis.residuals.forEach((row) => rows.push([JSON.stringify(row.label || ""), row.x, row.observed, row.error, row.sigma, row.included, row.residual, row.standardized].join(",")));
  const blob = new Blob([`${rows.join("\n")}\n`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "supernova-hubble-residuals.csv"; link.click(); URL.revokeObjectURL(link.href);
}

function drawAll() {
  if (!analysis) return;
  drawHubble(); drawResiduals(); drawProfile();
}

worker.addEventListener("message", (event) => {
  if (event.data.runId !== latestRunId) return;
  if (event.data.error) { setStatus(`Analysis error: ${event.data.error}`, ""); return; }
  analysis = event.data.result;
  drawAll(); updateMetrics(); updateTable();
  setStatus(`${analysis.metrics.includedCount} light curves · analysis ready`, "ready");
});

worker.addEventListener("error", (event) => setStatus(`Worker error: ${event.message}`, ""));

const resizeObserver = new ResizeObserver(() => requestAnimationFrame(drawAll));
[elements.hubble, elements.residual, elements.profile].forEach((canvas) => resizeObserver.observe(canvas.parentElement));
if (document.fonts) document.fonts.ready.then(drawAll);

setTheme(document.documentElement.dataset.theme || "light", false);
bindCarousel();
loadUrlState();
bindControls();
fetch("data/reference.json")
  .then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
  .then((data) => { reference = data; setStatus("Computing profile likelihood", "working"); runAnalysis(); })
  .catch((error) => setStatus(`Reference data unavailable: ${error.message}`, ""));
