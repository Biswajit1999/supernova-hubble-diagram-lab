# Supernova Hubble Diagram Lab

Distance modulus, cosmological acceleration and residual diagnostics.

Created and maintained by Biswajit Jana. Private research code — not for redistribution.

## Scientific Purpose

This zero-build browser laboratory puts a compact reference-data bundle in front of a flat
LCDM (Lambda-Cold-Dark-Matter) simulation of the Type Ia supernova Hubble diagram. The app loads
`data/reference.json`, renders those published anchors first, then sends the adjustable model
parameters to `physicsWorker.js` so the numerical integration stays off the UI thread.

## Background: The Hubble Diagram and Standardizable Candles

A Hubble diagram plots a distance indicator (here, distance modulus `mu`) against redshift `z`
for a population of objects. Its shape encodes the expansion history of the universe: at low
redshift the relation is linear (Hubble's law), and at higher redshift it curves in a way that is
sensitive to the universe's matter and dark-energy content.

Type Ia supernovae are used as "standardizable candles" because their peak luminosity, after
light-curve-shape and color corrections, is nearly uniform across events. That makes them one of
the few tracers luminous enough to be seen at cosmological distances (z ~ 0.01-2) while still
having a distance precision of a few percent per object. This is the observational channel that
first revealed the accelerating expansion of the universe (Riess et al. 1998; Perlmutter et al.
1999), which in the standard cosmological model is attributed to a dark-energy term,
Lambda (the cosmological constant).

### Distance modulus

The distance modulus relates apparent magnitude `m` to absolute magnitude `M` and luminosity
distance `d_L` (in parsecs):

```
mu = m - M = 5 * log10(d_L / 10 pc)
```

Equivalently, with `d_L` in Mpc:

```
mu = 5 * log10(d_L) + 25
```

### Luminosity distance in flat LCDM

For a spatially flat universe with matter density parameter `Omega_m` and dark-energy density
`Omega_Lambda = 1 - Omega_m`, the dimensionless Hubble expansion rate is:

```
E(z) = sqrt( Omega_m * (1 + z)^3 + (1 - Omega_m) )
```

The comoving distance is the integral of `c / (H0 * E(z))` from 0 to `z`, and for a flat
universe the luminosity distance is simply that comoving distance scaled by `(1 + z)`:

```
d_C(z) = (c / H0) * Integral[ 1 / E(z'), {z', 0, z} ]
d_L(z) = (1 + z) * d_C(z)
```

Combining these gives the model curve fit by this lab:

```
mu(z) = 5 * log10[ (1 + z) * (c / H0) * Integral(1/E(z'), 0, z) ] + 25 + M_bias
```

where `c` is the speed of light in km/s, `H0` is the Hubble constant in km/s/Mpc, and `M_bias`
is an adjustable magnitude offset representing residual calibration/standardization systematics.

### LCDM parameters

- **H0** (Hubble constant, km/s/Mpc): the present-day expansion rate. Planck 2018 (Planck
  Collaboration et al. 2020) infers `H0 ~ 67.4` km/s/Mpc from the CMB, in mild ("Hubble") tension
  with local distance-ladder measurements around 73 km/s/Mpc.
- **Omega_m** (matter density parameter): fraction of the critical density in matter (baryonic +
  dark). Planck 2018 gives `Omega_m ~ 0.315`.
- **Omega_Lambda** (dark-energy density parameter): `1 - Omega_m` in the flat model used here
  (`~ 0.685` from Planck 2018), driving the late-time acceleration.

## How It Works

1. **Reference data.** `data/reference.json` stores a 180-supernova stratified subsample drawn
   directly from the public **Pantheon+SH0ES** data release (Scolnic et al. 2022; Brout et al.
   2022; `PantheonPlusSH0ES/DataRelease` on GitHub), spanning the full survey redshift range
   `z = 0.0012` to `z = 2.26`, with each point's real 1-sigma distance-modulus uncertainty
   (`MU_SH0ES_ERR_DIAG`) carried through and rendered as an error bar. These 1701 real,
   individually-fit supernovae (subsampled to 180 for browser rendering) load and render first,
   before any simulation runs, so the model is always shown against actual observational data
   rather than a synthetic stand-in.
2. **Interactive parameters.** `app.js` builds range-slider controls for `H0`, `Omega_m`, a
   magnitude offset `M_bias`, and an intrinsic scatter term, all defined in the `LAB.controls`
   table.
3. **Worker-side model.** Every parameter change posts a message to `physicsWorker.js`, which:
   - Numerically integrates `1 / E(z)` with the trapezoid rule (`trap()`, 300 subintervals) to
     get the comoving distance at 500 redshift points from `z = 0.01` to `z = 1.5`.
   - Evaluates `mu(z)` from the distance-modulus/luminosity-distance relation above.
   - Reports summary metrics: `mu` at `z = 1`, the deceleration parameter
     `q0 = 1.5 * Omega_m - 1` (its sign flips from decelerating to accelerating near
     `Omega_m = 2/3`), the current scatter setting, and `ref_rms_mag` — the RMS of the
     model-minus-reference residuals (in magnitudes) evaluated at each of the five reference
     anchor redshifts, giving a quick goodness-of-fit readout as sliders move.
   - Generates a diagnostic heatmap ("Hubble residual field") showing
     `|mu_model(z) - mu_grid| / 9` over a `z`-by-`mu` grid, giving a quick visual sense of where a
     given parameter choice is consistent with a plausible Hubble-diagram region.
4. **Rendering.** `app.js` draws the reference anchors and the model curve on a shared canvas
   (`drawSeries`), and the worker's residual field on a second canvas (`drawHeatmap`), at up to
   the browser's native frame rate; `research-overlay.js` adds a non-invasive validation/telemetry
   panel on top.
5. **Repository validation.** `scripts/validate.js` and `scripts/validate_repository.mjs` check
   that required files exist, that `data/reference.json` and `data/research-reference.json`
   parse and contain finite anchors, that the worker is syntactically valid, that citations are
   present, and that no unfinished scaffold tokens remain — all without a network connection or
   build step.

## Architecture

- `index.html`: mission-control interface.
- `styles.css`: dense dark scientific dashboard.
- `app.js`: UI state, Canvas rendering and worker orchestration.
- `physicsWorker.js`: numerical model (including the flat-LCDM `supernova()` function) and
  heatmap generation.
- `research-overlay.js`: non-invasive validation/telemetry panel.
- `data/reference.json`: small auditable Pantheon-style reference-data bundle.
- `data/research-reference.json`: benchmark anchors used by the repository validator.
- `scripts/validate.js`, `scripts/validate_repository.mjs`: no-dependency repository validation.

## Usage

```bash
python -m http.server 8080
```

Open `http://localhost:8080`. Drag the `H0`, `Omega_m`, magnitude-offset and scatter sliders to
see the model curve and residual heatmap update live against the fixed reference anchors, or
click **Reset model** to return to the default parameters (`H0 = 70`, `Omega_m = 0.3`).

## Validate

```bash
npm run check
```

The validation script checks required files, JSON reference data, worker syntax, citations and
absence of unfinished scaffold tokens.

## Physics/Math Appendix

Flat LCDM distance-modulus model, as implemented in `physicsWorker.js`:

```
E(z)      = sqrt( Omega_m (1+z)^3 + (1 - Omega_m) )

d_C(z)    = (c / H0) * Integral_0^z [ 1 / E(z') ] dz'      (comoving distance, flat space)

d_L(z)    = (1 + z) * d_C(z)                                 (luminosity distance)

mu(z)     = 5 log10( d_L(z) ) + 25 + M_bias                  (distance modulus, d_L in Mpc)

q0        = 1.5 * Omega_m - 1                                 (present-day deceleration parameter,
                                                                 flat LCDM, negative => acceleration)
```

Constants used: `c = 299792.458` km/s (`physicsWorker.js`, `const C`).

The residual/response heatmap evaluates `|mu(z) - mu_grid| / 9` over a `72 x 72` grid spanning
`z in [0.1, 1.3]` and `mu in [36, 45]`, normalized to `[0, 1]` for display.

## Reference Data

Representative binned distance-modulus anchors for browser validation against published Type Ia
supernova Hubble diagrams (Pantheon-style, Scolnic et al. 2018).

## References

- Riess, A.G. et al., 1998. Observational evidence from supernovae for an accelerating universe
  and a cosmological constant. The Astronomical Journal, 116(3), pp.1009-1038.
- Perlmutter, S. et al., 1999. Measurements of Omega and Lambda from 42 high-redshift supernovae.
  The Astrophysical Journal, 517(2), pp.565-586.
- Scolnic, D.M. et al., 2018. The complete light-curve sample of spectroscopically confirmed SNe
  Ia from Pan-STARRS1 and cosmological constraints from the combined Pantheon sample. The
  Astrophysical Journal, 859(2), p.101.
- Scolnic, D. et al., 2022. The Pantheon+ Analysis: The Full Data Set and Light-curve Release.
  The Astrophysical Journal, 938(2), p.113. (source of the 180-point reference sample used here;
  data release: https://github.com/PantheonPlusSH0ES/DataRelease)
- Brout, D. et al., 2022. The Pantheon+ Analysis: Cosmological Constraints. The Astrophysical
  Journal, 938(2), p.110.
- Planck Collaboration, Aghanim, N. et al., 2020. Planck 2018 results. VI. Cosmological
  parameters. Astronomy & Astrophysics, 641, A6.

## Reading the Plot

- **Main panel.** Yellow points are the 180 real Pantheon+SH0ES supernovae, each with a vertical
  1-sigma error bar from the survey's own light-curve fit uncertainty. The green curve is the
  live flat-LCDM model at the current slider values.
- **Fit residuals panel.** Plots `mu_model(z) - mu_observed(z)` for every reference supernova, so
  systematic mismatch (a slope or offset in the residuals) is visible directly rather than having
  to eyeball it off the main distance-modulus curve. Points beyond +/-0.3 mag are flagged red.
- **`ref_rms_mag` telemetry.** The RMS of the residuals above, in magnitudes — a single number
  for how well the current `H0`/`Omega_m`/`M_bias` combination fits the real data.

## What the Data Actually Show: Quantifying Cosmic Acceleration

Two more telemetry values go beyond fitting one model curve by hand: `bestfit_omegaM` and
`acceleration_signal_mag` are computed by an automatic grid search (`accelerationEvidence()`
in `physicsWorker.js`) that scans `Omega_m` from 0 to 1 at the current `H0`/`M_bias`, finds the
value that best fits the real 180-supernova sample, and directly compares it to the historically
important **`Omega_m = 1` matter-only universe** — a purely decelerating expansion with no dark
energy, which is exactly the model Riess (1998) and Perlmutter (1999) showed was inconsistent
with real Type Ia data.

- `bestfit_omegaM` is the matter-density fraction that minimises the RMS residual against the
  real Pantheon+SH0ES points at the current `H0`. (At fixed `H0 = 70`, `M_bias = 0` this lands
  near `Omega_m ~ 0.48` — higher than the Planck value of `~0.315` because this simple one-parameter
  grid search does not simultaneously marginalise over `H0`, unlike the full Pantheon+ cosmological
  fit; the qualitative acceleration signal below is unaffected by that simplification.)
- `acceleration_signal_mag` is the distance-modulus offset, at `z = 1`, between that best-fit
  curve and the `Omega_m = 1` matter-only curve. A positive value means the real supernovae sit
  **farther away (fainter) than a decelerating universe predicts** — the same qualitative
  signature, read directly off real data, that first indicated the expansion of the universe is
  accelerating rather than slowing down.

This turns the lab from "here is a curve you can drag sliders on" into "here is what the real
data rule out, and by how much," using the same logic as the original discovery papers.

## Research Quality Upgrade

See [RESEARCH_QUALITY.md](RESEARCH_QUALITY.md) for the validation layer, reference anchors,
equations and research boundaries added to this repository.
