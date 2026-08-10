# Supernova Hubble Diagram Lab

Distance modulus, cosmological acceleration and residual diagnostics.

Created and maintained by Biswajit Jana.

## Scientific Purpose

This zero-build browser laboratory puts a compact reference-data bundle in front of the simulation. The app loads `data/reference.json`, renders those published anchors first, then sends the adjustable model to `physicsWorker.js` so numerical work stays off the UI thread.

## Architecture

- `index.html`: mission-control interface.
- `styles.css`: dense dark scientific dashboard.
- `app.js`: UI state, Canvas rendering and worker orchestration.
- `physicsWorker.js`: numerical model and heatmap generation.
- `data/reference.json`: small auditable reference-data bundle.
- `scripts/validate.js`: no-dependency repository validation.

## Run

```bash
python -m http.server 8080
```

Open `http://localhost:8080`.

## Validate

```bash
npm run check
```

The validation script checks required files, JSON reference data, worker syntax, citations and absence of unfinished scaffold tokens.

## Reference Data

Representative binned distance-modulus anchors for browser validation against published Type Ia supernova Hubble diagrams.

## References

- Riess, A.G. et al., 1998. Observational evidence from supernovae for an accelerating universe and a cosmological constant. The Astronomical Journal, 116(3), pp.1009-1038.
- Scolnic, D.M. et al., 2018. The complete light-curve sample of spectroscopically confirmed SNe Ia from Pan-STARRS1 and cosmological constraints from the combined Pantheon sample. The Astrophysical Journal, 859(2), p.101.
