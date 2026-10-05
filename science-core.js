(function attachSupernovaScience(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.SupernovaScience = api;
}(typeof globalThis !== "undefined" ? globalThis : self, function buildScienceCore() {
  "use strict";

  const C_KM_S = 299792.458;
  const integralCache = new Map();

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function expansionRate(z, omegaM) {
    return Math.sqrt(omegaM * Math.pow(1 + z, 3) + (1 - omegaM));
  }

  function comovingIntegral(z, omegaM) {
    const key = `${omegaM.toFixed(5)}:${z.toFixed(7)}`;
    if (integralCache.has(key)) return integralCache.get(key);
    const steps = Math.max(80, Math.ceil(120 * z));
    const evenSteps = steps % 2 === 0 ? steps : steps + 1;
    const h = z / evenSteps;
    let sum = 1 / expansionRate(0, omegaM) + 1 / expansionRate(z, omegaM);
    for (let i = 1; i < evenSteps; i += 1) {
      sum += (i % 2 === 0 ? 2 : 4) / expansionRate(i * h, omegaM);
    }
    const integral = sum * h / 3;
    integralCache.set(key, integral);
    return integral;
  }

  function distanceModulus(z, omegaM, h0) {
    if (!(z > 0) || !(omegaM >= 0 && omegaM <= 1) || !(h0 > 0)) return NaN;
    const luminosityDistanceMpc = (1 + z) * (C_KM_S / h0) * comovingIntegral(z, omegaM);
    return 5 * Math.log10(luminosityDistanceMpc) + 25;
  }

  function effectiveSigma(point, intrinsicScatter) {
    return Math.sqrt(Math.pow(Number(point.y_err) || 0, 2) + Math.pow(intrinsicScatter, 2));
  }

  function selectPoints(points, zMin) {
    return points.filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y) && point.x >= zMin);
  }

  function profileMagnitudeOffset(points, omegaM, h0, intrinsicScatter, zMin) {
    const selected = selectPoints(points, zMin);
    let weightedResidual = 0;
    let weightSum = 0;
    const rows = [];
    for (const point of selected) {
      const base = distanceModulus(point.x, omegaM, h0);
      const sigma = effectiveSigma(point, intrinsicScatter);
      const weight = 1 / (sigma * sigma);
      const residual = point.y - base;
      weightedResidual += weight * residual;
      weightSum += weight;
      rows.push({ residual, weight });
    }
    const offset = weightSum > 0 ? weightedResidual / weightSum : 0;
    const chi2 = rows.reduce((sum, row) => sum + row.weight * Math.pow(row.residual - offset, 2), 0);
    return { offset, chi2, count: selected.length };
  }

  function chiSquare(points, omegaM, h0, offset, intrinsicScatter, zMin) {
    let chi2 = 0;
    let count = 0;
    for (const point of points) {
      if (point.x < zMin) continue;
      const sigma = effectiveSigma(point, intrinsicScatter);
      const residual = point.y - (distanceModulus(point.x, omegaM, h0) + offset);
      chi2 += Math.pow(residual / sigma, 2);
      count += 1;
    }
    return { chi2, count };
  }

  function crossing(profile, minimumIndex, threshold, direction) {
    let i = minimumIndex;
    while (i >= 0 && i < profile.length && profile[i].deltaChi2 <= threshold) i += direction;
    if (i < 0 || i >= profile.length) return null;
    const insideIndex = i - direction;
    const outside = profile[i];
    const inside = profile[insideIndex];
    const fraction = (threshold - inside.deltaChi2) / (outside.deltaChi2 - inside.deltaChi2);
    return inside.omegaM + fraction * (outside.omegaM - inside.omegaM);
  }

  function profileLikelihood(points, h0, intrinsicScatter, zMin) {
    const raw = [];
    for (let i = 0; i <= 190; i += 1) {
      const omegaM = Number((0.05 + i * 0.005).toFixed(3));
      const result = profileMagnitudeOffset(points, omegaM, h0, intrinsicScatter, zMin);
      raw.push({ omegaM, chi2: result.chi2, offset: result.offset });
    }
    let minimumIndex = 0;
    for (let i = 1; i < raw.length; i += 1) if (raw[i].chi2 < raw[minimumIndex].chi2) minimumIndex = i;
    const minimum = raw[minimumIndex];
    const profile = raw.map((entry) => ({ ...entry, deltaChi2: entry.chi2 - minimum.chi2 }));
    const matter = profile[profile.length - 1];
    return {
      profile,
      bestOmegaM: minimum.omegaM,
      bestOffset: minimum.offset,
      minimumChi2: minimum.chi2,
      intervalLow: crossing(profile, minimumIndex, 1, -1),
      intervalHigh: crossing(profile, minimumIndex, 1, 1),
      matterDeltaChi2: matter.deltaChi2,
      matterOffset: matter.offset
    };
  }

  function logarithmicSeries(minimum, maximum, count) {
    const low = Math.log10(minimum);
    const high = Math.log10(maximum);
    return Array.from({ length: count }, (_, index) => Math.pow(10, low + (high - low) * index / (count - 1)));
  }

  function analyze(points, inputParams) {
    const params = {
      omegaM: clamp(Number(inputParams.omegaM) || 0.3, 0.05, 1),
      h0: clamp(Number(inputParams.h0) || 70, 40, 100),
      intrinsicScatter: clamp(Number(inputParams.intrinsicScatter) || 0, 0, 1),
      manualOffset: clamp(Number(inputParams.manualOffset) || 0, -5, 5),
      profileOffset: inputParams.profileOffset !== false,
      zMin: clamp(Number(inputParams.zMin) || 0.01, 0, 1)
    };
    const profileResult = profileLikelihood(points, params.h0, params.intrinsicScatter, params.zMin);
    const currentProfile = profileMagnitudeOffset(points, params.omegaM, params.h0, params.intrinsicScatter, params.zMin);
    const effectiveOffset = params.profileOffset ? currentProfile.offset : params.manualOffset;
    const currentFit = chiSquare(points, params.omegaM, params.h0, effectiveOffset, params.intrinsicScatter, params.zMin);
    const redshifts = logarithmicSeries(Math.max(0.001, Math.min(...points.map((point) => point.x))), Math.max(...points.map((point) => point.x)) * 1.03, 520);
    const model = redshifts.map((z) => ({ x: z, y: distanceModulus(z, params.omegaM, params.h0) + effectiveOffset }));
    const matterModel = redshifts.map((z) => ({ x: z, y: distanceModulus(z, 1, params.h0) + profileResult.matterOffset }));
    const residuals = points.map((point) => {
      const sigma = effectiveSigma(point, params.intrinsicScatter);
      const residual = point.y - (distanceModulus(point.x, params.omegaM, params.h0) + effectiveOffset);
      return { label: point.label, x: point.x, observed: point.y, error: point.y_err, sigma, residual, standardized: residual / sigma, included: point.x >= params.zMin };
    });
    const q0 = 1.5 * params.omegaM - 1;
    const transitionRedshift = params.omegaM > 0 && params.omegaM < 2 / 3
      ? Math.cbrt(2 * (1 - params.omegaM) / params.omegaM) - 1
      : null;
    return {
      params,
      model,
      matterModel,
      residuals,
      profile: profileResult.profile,
      metrics: {
        includedCount: currentFit.count,
        excludedCount: points.length - currentFit.count,
        effectiveOffset,
        currentChi2: currentFit.chi2,
        chi2PerDatum: currentFit.count ? currentFit.chi2 / currentFit.count : NaN,
        bestOmegaM: profileResult.bestOmegaM,
        bestOffset: profileResult.bestOffset,
        intervalLow: profileResult.intervalLow,
        intervalHigh: profileResult.intervalHigh,
        matterDeltaChi2: profileResult.matterDeltaChi2,
        q0,
        transitionRedshift
      }
    };
  }

  return {
    C_KM_S,
    analyze,
    chiSquare,
    distanceModulus,
    expansionRate,
    profileLikelihood,
    profileMagnitudeOffset
  };
}));
