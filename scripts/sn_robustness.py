"""Independent redshift-selection and covariance stress tests for the 180-row Pantheon+ display subset.

This is NOT the Pantheon+ likelihood: repeated-SN correlations, calibration covariance,
peculiar-velocity covariance, and selection-function nuisance terms are absent.
The rank-one covariance below is a hypothetical, labelled sensitivity experiment.
"""
from __future__ import annotations

import argparse
import json
import math
from functools import lru_cache
from pathlib import Path

C_KM_S = 299792.458
ROOT = Path(__file__).resolve().parents[1]


def load_points(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    points = data["points"]
    if len(points) != data["n_points"]:
        raise ValueError("Reference row count disagrees with provenance")
    for row in points:
        if not all(math.isfinite(float(row[key])) for key in ("x", "y", "y_err")):
            raise ValueError("Non-finite observation")
        if row["x"] <= 0 or row["y_err"] <= 0:
            raise ValueError("Redshifts and uncertainties must be positive")
    return points


@lru_cache(maxsize=30000)
def distance_modulus(z: float, omega_m: float, h0: float = 70.0) -> float:
    if not (z > 0 and 0 <= omega_m <= 1 and h0 > 0):
        raise ValueError("Invalid flat-LCDM parameters")
    n = max(80, math.ceil(120 * z))
    n += n % 2
    step = z / n

    def inv_e(zz: float) -> float:
        return 1.0 / math.sqrt(omega_m * (1 + zz) ** 3 + (1 - omega_m))

    integral = inv_e(0) + inv_e(z)
    integral += sum((4 if i % 2 else 2) * inv_e(i * step) for i in range(1, n))
    dl_mpc = (1 + z) * (C_KM_S / h0) * integral * step / 3
    return 5 * math.log10(dl_mpc) + 25


def inverse_covariance_product(vector: list[float], sigmas: list[float],
                               shape: list[float], tau: float) -> list[float]:
    """Sherman-Morrison for C=diag(sigma**2)+tau**2*shape*shape.T."""
    if tau < 0 or len(vector) != len(sigmas) or len(vector) != len(shape):
        raise ValueError("Invalid covariance dimensions or amplitude")
    if any(s <= 0 or not math.isfinite(s) for s in sigmas):
        raise ValueError("Invalid diagonal errors")
    inv = [1 / (s * s) for s in sigmas]
    projection = sum(w * v * x for w, v, x in zip(inv, shape, vector))
    denominator = 1 + tau * tau * sum(w * v * v for w, v in zip(inv, shape))
    return [w * (x - tau * tau * v * projection / denominator)
            for w, v, x in zip(inv, shape, vector)]


def profile_offset(rows: list[dict], omega_m: float, scatter: float = 0.1,
                   tau: float = 0.0, shape_mode: str = "redshift",
                   h0: float = 70.0) -> dict:
    if not rows or scatter < 0:
        raise ValueError("Need nonempty sample and nonnegative scatter")
    sigmas = [math.hypot(float(r["y_err"]), scatter) for r in rows]
    residuals = [float(r["y"]) - distance_modulus(float(r["x"]), omega_m, h0)
                 for r in rows]
    if shape_mode == "constant":
        shape = [1.0] * len(rows)
    elif shape_mode == "redshift":
        shape = [float(r["x"]) / (1 + float(r["x"])) for r in rows]
    else:
        raise ValueError("Unknown covariance mode")
    ones = [1.0] * len(rows)
    inv_r = inverse_covariance_product(residuals, sigmas, shape, tau)
    inv_one = inverse_covariance_product(ones, sigmas, shape, tau)
    denom = sum(inv_one)
    if denom <= 0:
        raise ArithmeticError("Non-positive profiled offset precision")
    offset = sum(inv_r) / denom
    centred = [r - offset for r in residuals]
    inv_centred = inverse_covariance_product(centred, sigmas, shape, tau)
    chi2 = sum(x * y for x, y in zip(centred, inv_centred))
    return {"omega_m": omega_m, "offset_mag": offset, "chi2": max(0.0, chi2),
            "n": len(rows)}


def grid_fit(rows: list[dict], scatter: float = 0.1, tau: float = 0.0,
             shape_mode: str = "redshift", h0: float = 70.0) -> dict:
    grid = [round(0.05 + 0.01 * i, 2) for i in range(96)]
    fits = [profile_offset(rows, om, scatter, tau, shape_mode, h0) for om in grid]
    winner = min(fits, key=lambda x: x["chi2"])
    return {**winner, "grid_step_omega_m": 0.01}


def run_audit(points: list[dict]) -> dict:
    selected = sorted((p for p in points if p["x"] >= 0.01), key=lambda p: p["x"])
    baseline = grid_fit(selected)
    cuts = [{"z_min": cut, **grid_fit([p for p in points if p["x"] >= cut])}
            for cut in (0.01, 0.03, 0.05, 0.1)]
    deletions = []
    for block in range(5):
        start = len(selected) * block // 5
        end = len(selected) * (block + 1) // 5
        retained = selected[:start] + selected[end:]
        deletions.append({"removed_redshift_quintile": block + 1,
                          "n_removed": end - start, **grid_fit(retained)})
    covariance = [{"tau_mag": tau, **grid_fit(selected, tau=tau)}
                  for tau in (0.0, 0.02, 0.05, 0.1)]
    return {
        "scope": "180-row Pantheon+SH0ES teaching subset; NOT full likelihood",
        "n_input": len(points), "n_baseline": len(selected),
        "assumed_intrinsic_scatter_mag": 0.1,
        "covariance_model": "hypothetical diagonal plus rank-one redshift ramp",
        "redshift_ramp": "v(z)=z/(1+z); Cij=delta_ij*(err_i^2+0.1^2)+tau^2*v_i*v_j",
        "baseline": baseline, "redshift_cuts": cuts,
        "leave_one_redshift_quintile_out": deletions,
        "correlated_systematic_sensitivity": covariance,
        "limitations": [
            "No Pantheon+ full covariance or Cepheid calibration.",
            "Repeated light curves are not grouped by supernova.",
            "Grid precision is 0.01 in Omega_m; no population confidence intervals.",
            "Correlated systematic is illustrative, not measured."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_audit(load_points(ROOT / "data" / "reference.json"))
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
