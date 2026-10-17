"""Independent Python diagnostics for the Pantheon+ Hubble-diagram demonstrator.

This does not reproduce the official Pantheon+ likelihood: the browser's 180-row
subset omits full systematic covariance, calibration, and repeated-event modeling.
Full covariance inputs here are user-supplied sensitivity *scenarios*.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad, simpson
from scipy.linalg import solve_triangular

C_KM_S = 299792.458


def expansion_rate(z: np.ndarray | float, omega_m: float) -> np.ndarray | float:
    if not 0 <= omega_m <= 1 or not np.all(np.isfinite(z)) or np.any(np.asarray(z) < 0):
        raise ValueError("Require flat LCDM with 0<=omega_m<=1 and nonnegative finite redshift")
    return np.sqrt(omega_m * (1 + np.asarray(z)) ** 3 + 1 - omega_m)


def distance_modulus(z: np.ndarray | float, omega_m: float, h0: float = 70,
                     method: str = "quad", steps: int = 256) -> np.ndarray | float:
    """Flat-LCDM distance modulus; quad or composite Simpson integration."""
    z_values = np.asarray(z, dtype=float)
    if not np.all(np.isfinite(z_values)) or np.any(z_values <= 0) or not np.isfinite(h0) or h0 <= 0:
        raise ValueError("Redshift and H0 must be finite and strictly positive")
    if method not in ("quad", "simpson") or (method == "simpson" and (steps < 4 or steps % 2)):
        raise ValueError("Choose quad or Simpson with an even number of >=4 panels")
    def one(zz: float) -> float:
        if method == "quad":
            integral = quad(lambda t: 1 / expansion_rate(t, omega_m), 0, zz,
                            epsabs=1e-11, epsrel=1e-11)[0]
        else:
            grid = np.linspace(0, zz, steps + 1)
            integral = simpson(1 / expansion_rate(grid, omega_m), x=grid)
        return float(5 * np.log10((1 + zz) * C_KM_S * integral / h0) + 25)
    result = np.asarray([one(float(value)) for value in z_values.flat]).reshape(z_values.shape)
    return float(result) if z_values.ndim == 0 else result


def covariance_from_errors(z: np.ndarray, sigma: np.ndarray, correlation: float = 0.0,
                           length_z: float = 0.1) -> np.ndarray:
    """Illustrative correlated covariance; not the Pantheon+ released matrix."""
    z, sigma = np.asarray(z, float), np.asarray(sigma, float)
    if z.ndim != 1 or z.size < 5 or sigma.shape != z.shape:
        raise ValueError("Expected >=5 observations with matching uncertainties")
    if np.any(sigma <= 0) or not np.all(np.isfinite(sigma)) or not np.all(np.isfinite(z)):
        raise ValueError("Uncertainties must be finite and positive")
    if not np.isfinite(correlation) or not 0 <= correlation < 1 or not np.isfinite(length_z) or length_z <= 0:
        raise ValueError("Require 0<=correlation<1 and positive finite length_z")
    kernel = np.exp(-np.abs(z[:, None] - z[None, :]) / length_z)
    return np.outer(sigma, sigma) * ((1 - correlation) * np.eye(len(z)) + correlation * kernel)


def profile_offset(z: np.ndarray, mu: np.ndarray, covariance: np.ndarray,
                   omega_m: float, h0: float = 70, method: str = "quad") -> dict:
    """Analytic generalized-least-squares magnitude offset and chi-square.

    The H0/absolute-magnitude degeneracy is exact when the offset is free.
    """
    z, mu, cov = np.asarray(z, float), np.asarray(mu, float), np.asarray(covariance, float)
    if z.ndim != 1 or mu.shape != z.shape or cov.shape != (len(z), len(z)) or len(z) < 5:
        raise ValueError("Incompatible data/covariance dimensions")
    if not np.all(np.isfinite(mu)) or not np.all(np.isfinite(cov)) or not np.allclose(cov, cov.T, atol=1e-12):
        raise ValueError("Nonfinite or asymmetric covariance/data")
    chol = np.linalg.cholesky(cov)
    residual = mu - distance_modulus(z, omega_m, h0, method=method)
    whitened = solve_triangular(chol, residual, lower=True)
    whitened_ones = solve_triangular(chol, np.ones(len(z)), lower=True)
    denom = float(whitened_ones @ whitened_ones)
    offset = float((whitened_ones @ whitened) / denom)
    whitened_centered = whitened - offset * whitened_ones
    chi2 = float(whitened_centered @ whitened_centered)
    logdet = float(2 * np.log(np.diag(chol)).sum())
    return {"omega_m": omega_m, "h0": h0, "offset": offset, "offset_se": denom ** -0.5,
            "chi2": chi2, "log_likelihood": -0.5 * (chi2 + logdet + len(z) * np.log(2 * np.pi)),
            "n_observations": len(z)}


def profile_omega(z: np.ndarray, mu: np.ndarray, covariance: np.ndarray,
                  omega_grid: np.ndarray | None = None, h0: float = 70) -> dict:
    """Profile omega_m with a free magnitude offset, returning grid Δchi²."""
    grid = np.asarray(np.linspace(0.05, 1.0, 96) if omega_grid is None else omega_grid, float)
    if grid.ndim != 1 or len(grid) < 3 or not np.all(np.diff(grid) > 0) or grid[0] < 0 or grid[-1] > 1:
        raise ValueError("Grid must be increasing and contained within [0,1]")
    rows = [profile_offset(z, mu, covariance, float(value), h0) for value in grid]
    values = np.array([row["chi2"] for row in rows])
    best = int(np.argmin(values))
    return {"best_omega_m": float(grid[best]), "best_offset": rows[best]["offset"],
            "minimum_chi2": float(values[best]), "omega_grid": grid.tolist(),
            "delta_chi2": (values - values[best]).tolist(), "n_observations": len(z),
            "grid_boundary_minimum": bool(best in (0, len(grid) - 1))}


def redshift_cut_sensitivity(z: np.ndarray, mu: np.ndarray, covariance: np.ndarray,
                             cuts: tuple[float, ...] = (0.01, 0.03, 0.05, 0.1),
                             omega_grid: np.ndarray | None = None) -> list[dict]:
    """Re-profile after applying low-z cuts, using exact covariance submatrices."""
    z, mu, covariance = np.asarray(z), np.asarray(mu), np.asarray(covariance)
    rows = []
    for cut in cuts:
        mask = z >= cut
        if np.count_nonzero(mask) < 5:
            rows.append({"z_min": cut, "status": "insufficient_rows", "n_observations": int(mask.sum())})
            continue
        result = profile_omega(z[mask], mu[mask], covariance[np.ix_(mask, mask)], omega_grid)
        rows.append({"z_min": cut, "status": "ok", **result})
    return rows


def redshift_bin_jackknife(z: np.ndarray, mu: np.ndarray, covariance: np.ndarray,
                           bins: int = 5, omega_grid: np.ndarray | None = None) -> dict:
    """Delete contiguous redshift-ranked bins to assess dependence on coverage."""
    if bins < 2 or bins > len(z) // 5:
        raise ValueError("Need >=2 bins with at least five observations per retained sample")
    order = np.argsort(z)
    groups = np.array_split(order, bins)
    baseline = profile_omega(z, mu, covariance, omega_grid)
    samples = []
    for i, group in enumerate(groups):
        mask = np.ones(len(z), dtype=bool)
        mask[group] = False
        fit = profile_omega(np.asarray(z)[mask], np.asarray(mu)[mask],
                            np.asarray(covariance)[np.ix_(mask, mask)], omega_grid)
        samples.append({"removed_bin": i, "removed_n": len(group),
                        "removed_z_min": float(np.min(np.asarray(z)[group])),
                        "removed_z_max": float(np.max(np.asarray(z)[group])),
                        "best_omega_m": fit["best_omega_m"],
                        "delta_from_full": fit["best_omega_m"] - baseline["best_omega_m"]})
    return {"full_best_omega_m": baseline["best_omega_m"], "bins": samples,
            "note": "Delete-bin sensitivity; not a calibrated confidence interval."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path(__file__).resolve().parents[1] / "data/reference.json")
    parser.add_argument("--correlation", type=float, default=0.0)
    parser.add_argument("--length-z", type=float, default=0.1)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    document = json.loads(args.reference.read_text(encoding="utf-8"))
    points = document["points"]
    z = np.asarray([point["x"] for point in points], float)
    mu = np.asarray([point["y"] for point in points], float)
    sigma = np.asarray([point["y_err"] for point in points], float)
    covariance = covariance_from_errors(z, sigma, args.correlation, args.length_z)
    grid = np.linspace(0.05, 1, 96)
    result = {"dataset": str(args.reference), "n_rows": len(z),
              "covariance_scenario": {"correlation": args.correlation, "length_z": args.length_z},
              "profile": profile_omega(z, mu, covariance, grid),
              "redshift_cuts": redshift_cut_sensitivity(z, mu, covariance, omega_grid=grid),
              "delete_bin": redshift_bin_jackknife(z, mu, covariance, omega_grid=grid),
              "limitations": ["Illustrative covariance, not full Pantheon+ statistical/systematic covariance.",
                              "Subset has repeated-event and selection effects not treated here.",
                              "Profiled magnitude offset prevents independent H0 inference."]}
    serialized = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
