# Redshift selection and hypothetical correlated-error audit

This is an independent Python cross-check of the 180-row Pantheon+SH0ES **display subset**, not a cosmological reanalysis of the full release. The browser's original model and reference table remain unchanged.

The Python script tests three different numerical questions. First, it profiles the magnitude zero point and flat-LCDM matter density at redshift cuts z >= 0.01, 0.03, 0.05, and 0.10. Second, it deletes one of five rank-ordered redshift groups at a time and refits, exposing leverage from specific redshift ranges. Third, it introduces a **hypothetical** correlated calibration vector v(z)=z/(1+z) with covariance C_ij = delta_ij (sigma_diag,i^2 + 0.1^2) + tau^2 v_i v_j, for tau = 0, 0.02, 0.05 and 0.10 magnitudes. A Sherman-Morrison inverse is used so the nuisance magnitude offset is correctly reprofiled under each covariance.

Reproduce with `python scripts/sn_robustness.py --output /tmp/sn_robustness.json` and `python -m unittest discover -s tests -p test_sn_robustness.py`. The matter-density grid is spaced by 0.01; its grid precision is not a parameter confidence interval. H0 remains degenerate with the nuisance magnitude zero point, tested numerically. A perfectly common-mode calibration uncertainty is absorbed by the profiled offset, also tested.

**Limitations:** The 180 rows are not independent supernovae in general. The official full statistical/systematic covariance, peculiar-velocity terms, bias corrections, Cepheid calibration and duplicate-supernova structure are not represented. The rank-one covariance is an illustrative stress test, not an estimate of actual Pantheon+ systematics. None of these diagnostics justifies a discovery significance, H0 measurement, or collaboration-level Omega_m constraint.

Primary source: Scolnic et al. (2022), ApJ 938, 113; Brout et al. (2022), ApJ 938, 110; https://github.com/PantheonPlusSH0ES/DataRelease.
