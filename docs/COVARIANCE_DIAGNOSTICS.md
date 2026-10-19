# Offline Hubble-diagram sensitivity checks

This standalone Python module does **not** change the browser likelihood. Install `numpy` and `pytest`, then run `python -m pytest tests/test_covariance_diagnostics.py` and `PYTHONPATH=. python scripts/run_covariance_diagnostics.py`. For a limited diagnostic on the repository's existing 180-row reference, use `PYTHONPATH=. python scripts/run_covariance_diagnostics.py --reference data/reference.json`.

Three substantive analyses:

1. **Nuisance magnitude profiling with correlated covariance.** For residual `r = mu_obs - mu_LCDM`, a positive-definite `C`, and `1` the constant vector, `offset_hat = (1^T C^-1 r)/(1^T C^-1 1)`, `sigma_offset = (1^T C^-1 1)^(-1/2)`, `chi2 = (r - offset_hat)^T C^-1 (r - offset_hat)`. Cholesky whitening avoids explicitly inverting `C`. An optional `U U^T` factor models a **hypothetical** low-rank common calibration term; it is *not* the released Pantheon+ covariance.
2. **Independent luminosity-distance quadrature:** Gauss-Legendre integration of the flat-LCDM `1/E(z)` comoving distance, including analytic limits for `Omega_m=0` and `Omega_m=1`, plus numerical convergence across quadrature orders.
3. **Redshift-bin deletion stability:** remove each redshift-quantile bin and recompute the entire diagonal-only `Omega_m` profile, including refitting the nuisance offset. This is not a cosmological parameter jackknife error bar.

The 180-row browser subset contains repeated light curves and is not a statistically independent sample of 180 SNe. The full Pantheon+ analysis includes correlations, selection corrections, peculiar velocities, and calibrated distances. This module neither reproduces that likelihood nor infers H0. With a free additive offset, changing H0 shifts the offset and leaves the profiled shape chi-square invariant. The toy common-mode amplitude (0.04 mag) is explicitly arbitrary. Interpret all CSV/JSON outputs as method diagnostics, not cosmological constraints or discovery significances.
