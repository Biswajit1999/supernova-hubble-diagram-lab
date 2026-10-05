"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const science = require("../science-core.js");

const reference = JSON.parse(fs.readFileSync("data/reference.json", "utf8"));

const mu70 = science.distanceModulus(0.5, 0.3, 70);
const mu75 = science.distanceModulus(0.5, 0.3, 75);
assert.ok(Number.isFinite(mu70) && mu70 > 40 && mu70 < 45, "distance modulus should be physical");
assert.ok(Math.abs((mu75 - mu70) - 5 * Math.log10(70 / 75)) < 1e-10, "H0 scaling must be exact");

const params = { omegaM: 0.3, h0: 70, intrinsicScatter: 0.1, profileOffset: true, zMin: 0.01 };
const analysis70 = science.analyze(reference.points, params);
const analysis75 = science.analyze(reference.points, { ...params, h0: 75 });

assert.equal(analysis70.residuals.length, reference.points.length, "every source point needs a residual");
assert.ok(analysis70.metrics.includedCount > 100, "the default cut should retain most light curves");
assert.ok(Math.abs(analysis70.metrics.q0 + 0.55) < 1e-12, "q0 must follow flat LCDM");
assert.ok(Math.abs(analysis70.metrics.bestOmegaM - analysis75.metrics.bestOmegaM) < 1e-12, "profiled Omega_m must be invariant to H0");
assert.ok(Math.abs(analysis70.metrics.currentChi2 - analysis75.metrics.currentChi2) < 1e-7, "profiled chi-square must be invariant to H0");
assert.ok(analysis70.metrics.matterDeltaChi2 >= 0, "matter-only delta chi-square cannot be negative");
assert.ok(analysis70.profile.every((row) => row.deltaChi2 >= -1e-8), "profile minimum must define zero");

console.log(
  `Science tests passed: ${analysis70.metrics.includedCount} included rows, ` +
  `best Omega_m=${analysis70.metrics.bestOmegaM.toFixed(3)}, ` +
  `matter-only delta chi-square=${analysis70.metrics.matterDeltaChi2.toFixed(2)}.`
);
