"use strict";

const fs = require("node:fs");
const crypto = require("node:crypto");

const required = [
  "README.md",
  "index.html",
  "styles.css",
  "app.js",
  "science-core.js",
  "physicsWorker.js",
  "data/reference.json",
  "scripts/build_reference_data.py",
  "scripts/test_science.js"
];
const failures = [];
for (const file of required) if (!fs.existsSync(file)) failures.push(`${file} missing`);

const reference = JSON.parse(fs.readFileSync("data/reference.json", "utf8"));
if (reference.n_points !== 180 || reference.points?.length !== 180) failures.push("reference subset must contain 180 points");
if (reference.n_full_sample !== 1701) failures.push("full-sample light-curve count must be documented as 1701");
if (reference.n_distinct_supernovae !== 1550) failures.push("distinct-supernova count must be documented as 1550");
if (!/^[a-f0-9]{64}$/.test(reference.source_file_sha256 || "")) failures.push("source SHA-256 is missing or malformed");

let previousRedshift = -Infinity;
for (const [index, point] of (reference.points || []).entries()) {
  if (![point.x, point.y, point.y_err].every(Number.isFinite)) failures.push(`point ${index} has non-finite values`);
  if (!(point.x > 0) || !(point.y_err > 0)) failures.push(`point ${index} has non-physical redshift/error`);
  if (point.x < previousRedshift) failures.push(`point ${index} breaks redshift ordering`);
  if (!point.label) failures.push(`point ${index} lacks an object identifier`);
  previousRedshift = point.x;
}

const html = fs.readFileSync("index.html", "utf8");
const requiredHtml = ["profile likelihood", "diagonal", "full covariance", "data-table-body"];
for (const phrase of requiredHtml) if (!html.toLowerCase().includes(phrase.toLowerCase())) failures.push(`index.html missing required disclosure: ${phrase}`);
if (html.includes("research-overlay.js")) failures.push("obsolete research overlay is still public");

const readme = fs.readFileSync("README.md", "utf8");
for (const citation of reference.requiredCitations || []) {
  const leadAuthor = citation.split(",")[0];
  if (!readme.includes(leadAuthor)) failures.push(`README missing citation family ${leadAuthor}`);
}

const combined = required.map((file) => fs.readFileSync(file, "utf8")).join("\n");
for (const token of ["TO" + "DO", "PLACE" + "HOLDER", "insert " + "logic", "coming " + "soon"]) {
  if (combined.toLowerCase().includes(token.toLowerCase())) failures.push(`unfinished token ${token}`);
}
const manifest = crypto.createHash("sha256").update(JSON.stringify(reference.points)).digest("hex").slice(0, 12);

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`Repository validation passed: ${reference.points.length} ordered anchors, manifest ${manifest}.`);
