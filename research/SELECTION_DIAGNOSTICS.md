# Conditional supernova Hubble diagnostics (18 November 2026)

Three independent calculations: (1) full-covariance GLS profiling of an additive magnitude offset, (2) sensitivity of its uncertainty to a shared calibration floor, and (3) nested redshift-cut offset estimates. The third calculation assumes independent errors; it does **not** implement the Pantheon+ covariance likelihood.

Run: `cd research && python -m unittest -v test_selection_diagnostics.py` (NumPy required).

The shared floor is mathematically degenerate with a freely profiled zero point; it increases the formal offset uncertainty but does not establish an absolute H0 calibration. The routines use controlled synthetic inputs and do not replace the repository's documented observational likelihood. No cosmological constraints or observational measurements are reported. AI-assisted implementation; Biswajit Jana is the requested sole Git author.