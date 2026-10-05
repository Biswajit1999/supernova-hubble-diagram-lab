# Supernova Hubble Diagram Laboratory

An uncertainty-aware, zero-build browser laboratory for exploring the Type Ia supernova Hubble diagram with a deterministic subset of the Pantheon+SH0ES distance release.

**Live laboratory:** https://biswajit1999.github.io/supernova-hubble-diagram-lab/

## Research question

After profiling over an unknown magnitude zero-point, how strongly does the redshift-dependent shape of a documented Pantheon+SH0ES subset prefer a low-density flat ΛCDM model over an `Ωm = 1` matter-only universe?

The project is a methods demonstrator. It is designed to make assumptions inspectable and to support intuition-building; it is not a replacement for the Pantheon+ collaboration likelihood.

## Data provenance

The official Pantheon+SH0ES distance table contains 1,701 light curves for 1,550 distinct Type Ia supernovae, spanning approximately `z = 0.001–2.26`. The browser bundle contains 180 rows selected deterministically:

1. Download `Pantheon+_Data/4_DISTANCES_AND_COVAR/Pantheon+SH0ES.dat` from the official release.
2. Verify the pinned SHA-256 checksum.
3. Sort the 1,701 rows by `zHD`.
4. Select row index `floor(i × (1701 − 1) / (180 − 1))` for `i = 0…179`.
5. Retain `CID`, `zHD`, `MU_SH0ES`, and `MU_SH0ES_ERR_DIAG`.

The selection is reproducible with:

```bash
python scripts/build_reference_data.py
```

The source checksum and column mapping are also stored in [`data/reference.json`](data/reference.json).

## Scientific model

For spatially flat ΛCDM,

```text
E(z) = sqrt[Ωm(1 + z)^3 + (1 − Ωm)]

dL(z) = (1 + z)(c/H0) ∫₀ᶻ dz′ / E(z′)

μmodel(z) = 5 log10[dL(z) / Mpc] + 25 + ΔM
```

The integral is evaluated with composite Simpson quadrature. The effective diagonal uncertainty is

```text
σeff,i² = σdiag,i² + σint².
```

For each value of `Ωm`, the nuisance magnitude offset is solved analytically:

```text
ΔM_hat = Σ wi [μobs,i − μbase,i] / Σ wi,
wi = 1 / σeff,i².
```

The displayed profile is then

```text
χ²(Ωm) = Σ [(μobs,i − μbase,i − ΔM_hat) / σeff,i]²,
Δχ²(Ωm) = χ²(Ωm) − χ²min.
```

The interval shown in the interface is the pair of grid crossings at `Δχ² = 1`. It is a conditional diagnostic under the simplified assumptions below, not a collaboration confidence interval.

## Why H0 is not inferred here

For an uncalibrated supernova Hubble diagram, changing `H0` shifts every distance modulus by a constant. That shift is exactly degenerate with the unknown absolute magnitude (represented by `ΔM`). When offset profiling is enabled, the `Ωm` profile is therefore invariant to `H0`, as it should be. An independent `H0` measurement requires an external absolute calibration such as Cepheid host distances and the corresponding covariance treatment.

## Deliberate limitations

This browser lab does **not**:

- use the full Pantheon+ statistical-plus-systematic covariance matrix;
- reproduce selection-bias, calibration, host-mass, or peculiar-velocity corrections;
- model correlations between repeated light curves or systematic groups;
- replace the full 1,701-light-curve likelihood with the 180-row display subset;
- derive a publication claim or convert `sqrt(Δχ²)` into a discovery significance;
- infer `H0` without an external absolute calibration.

The official data release includes covariance products. They are intentionally not bundled into this lightweight static application; this boundary is stated in the interface beside the result.

## Architecture

```text
index.html                   semantic application and methods narrative
styles.css                  responsive visual system and accessible states
app.js                      controls, charts, table, URL state, CSV export
science-core.js             testable cosmology and likelihood functions
physicsWorker.js            off-main-thread analysis adapter
data/reference.json         pinned 180-row browser subset and provenance
scripts/build_reference_data.py
                             deterministic source acquisition
scripts/test_science.js      numerical invariants and regression checks
scripts/validate.js          repository, disclosure, and data validation
```

No framework or build step is required. Computational work runs in a Web Worker so the interface remains responsive while the likelihood grid is evaluated.

## Run locally

Serve the repository root because browsers restrict worker and `fetch()` requests from `file://` URLs:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Verification

```bash
npm run check
```

The check runs JavaScript syntax validation, science regression tests, data-order and provenance assertions, required limitation disclosures, and unfinished-content detection.

Key tested invariants include:

- the exact `H0` scaling of distance modulus;
- `q0 = 1.5 Ωm − 1` for flat ΛCDM;
- non-negative `Δχ²` relative to the profile minimum;
- invariance of profiled `Ωm` and `χ²` under a change in `H0`;
- one residual for every bundled observation.

## Primary references

- Scolnic, D. et al. (2022), “The Pantheon+ Analysis: The Full Data Set and Light-curve Release,” *The Astrophysical Journal*, 938, 113. https://doi.org/10.3847/1538-4357/ac8b7a
- Brout, D. et al. (2022), “The Pantheon+ Analysis: Cosmological Constraints,” *The Astrophysical Journal*, 938, 110. https://doi.org/10.3847/1538-4357/ac8e04
- Riess, A. G. et al. (1998), “Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant,” *The Astronomical Journal*, 116, 1009. https://doi.org/10.1086/300499
- Perlmutter, S. et al. (1999), “Measurements of Ω and Λ from 42 High-Redshift Supernovae,” *The Astrophysical Journal*, 517, 565. https://doi.org/10.1086/307221
- Pantheon+SH0ES official data release: https://github.com/PantheonPlusSH0ES/DataRelease

## License

Project code is released under the MIT License. Upstream Pantheon+SH0ES data remain attributable to their authors and release repository; consult the upstream repository and papers when reusing those measurements.
