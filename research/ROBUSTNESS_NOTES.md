# Hubble-diagram numerical robustness (7 November 2026)

Run `cd research && python -m unittest -v test_hubble_robustness.py` with Python 3.10+ (no third-party packages).

Four conceptual checks: Simpson quadrature for flat ΛCDM luminosity distance; convergence with step refinement; analytic de Sitter (Ωm=0) distance; and the exact degeneracy of H0 with an unrestricted additive magnitude offset in a diagonal-error likelihood.

At z=1.8, Ωm=0.3, H0=70 km/s/Mpc, Simpson distances for 16, 32, 64, 128 and 256 intervals are approximately 13656.055677, 13656.070913, 13656.071853, 13656.071912 and 13656.071915 Mpc. The 1024-interval reference is 13656.071916 Mpc. This is a numerical convergence check, not an independent observational distance.

The offset profiler uses diagonal standard deviations only. It does not include Pantheon+ covariance, selection effects, repeated-SN correlations, or absolute calibration, and cannot determine H0 independently.

AI-assisted coding; scientific interpretation and review required before merging.
