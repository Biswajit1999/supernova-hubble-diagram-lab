"""Offline flat-LCDM Hubble-diagram diagnostics; not a Pantheon+ likelihood.

The optional low-rank systematic covariance is a *user-specified scenario*, not
an official calibration or peculiar-velocity covariance. Absolute magnitude and
H0 remain exactly degenerate after nuisance-offset profiling.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

C_KM_S = 299792.458


def luminosity_distance(z: np.ndarray, omega_m: float, h0: float = 70., order: int = 64) -> np.ndarray:
    """Flat-LCDM d_L [Mpc] using n-point Gauss-Legendre quadrature on [0,z]."""
    zz = np.asarray(z, dtype=float)
    if zz.ndim != 1 or not len(zz) or not np.isfinite(zz).all() or np.any(zz <= 0):
        raise ValueError('z must be a finite positive 1-D array')
    if not 0 <= omega_m <= 1 or not np.isfinite(h0) or h0 <= 0 or order < 2:
        raise ValueError('omega_m in [0,1], positive H0 and order>=2 required')
    x, w = np.polynomial.legendre.leggauss(order)
    sample_z = zz[:, None] * (x[None, :] + 1) / 2
    inv_e = 1 / np.sqrt(omega_m * (1 + sample_z)**3 + (1 - omega_m))
    integral = zz / 2 * (inv_e @ w)
    return (1 + zz) * (C_KM_S / h0) * integral


def distance_modulus(z: np.ndarray, omega_m: float, h0: float = 70., order: int = 64) -> np.ndarray:
    return 5 * np.log10(luminosity_distance(z, omega_m, h0, order)) + 25


def covariance_matrix(sigma: np.ndarray, intrinsic_scatter: float = 0.,
                      systematics: np.ndarray | None = None) -> np.ndarray:
    """C = diag(sigma^2+sigma_int^2) + U U^T (scenario covariance)."""
    s = np.asarray(sigma, dtype=float)
    if s.ndim != 1 or not len(s) or not np.isfinite(s).all() or np.any(s <= 0):
        raise ValueError('sigma must be finite, positive, 1-D')
    if not np.isfinite(intrinsic_scatter) or intrinsic_scatter < 0:
        raise ValueError('intrinsic_scatter must be nonnegative')
    c = np.diag(s*s + intrinsic_scatter**2)
    if systematics is not None:
        u = np.asarray(systematics, dtype=float)
        if u.ndim != 2 or u.shape[0] != len(s) or not np.isfinite(u).all():
            raise ValueError('systematics must be a finite (N,K) factor')
        c += u @ u.T
    return c


@dataclass(frozen=True)
class OffsetFit:
    offset: float
    offset_sigma: float
    chi2: float
    whitened_residuals: np.ndarray


class CovarianceProfiler:
    """Pre-factor a fixed SPD covariance; profile a single free additive offset."""
    def __init__(self, z: np.ndarray, mu: np.ndarray, covariance: np.ndarray):
        self.z = np.asarray(z, dtype=float)
        self.mu = np.asarray(mu, dtype=float)
        c = np.asarray(covariance, dtype=float)
        n = len(self.z)
        if self.z.shape != (n,) or self.mu.shape != (n,) or n < 3:
            raise ValueError('z and mu must be matching 1-D arrays with N>=3')
        if not np.isfinite(self.z).all() or not np.isfinite(self.mu).all() or np.any(self.z <= 0):
            raise ValueError('non-finite data or nonpositive redshifts')
        if c.shape != (n,n) or not np.isfinite(c).all() or not np.allclose(c,c.T,atol=1e-12):
            raise ValueError('covariance must be symmetric finite NxN')
        try:
            self.chol = np.linalg.cholesky(c)
        except np.linalg.LinAlgError as exc:
            raise ValueError('covariance must be positive definite') from exc
        self.ones_white = np.linalg.solve(self.chol, np.ones(n))
        self.denominator = float(self.ones_white @ self.ones_white)

    def fit(self, omega_m: float, h0: float = 70., order: int = 64) -> OffsetFit:
        residual = self.mu - distance_modulus(self.z, omega_m, h0, order)
        white = np.linalg.solve(self.chol, residual)
        offset = float(self.ones_white @ white / self.denominator)
        white -= offset * self.ones_white
        return OffsetFit(offset, self.denominator**(-0.5), float(white @ white), white)

    def grid_profile(self, omega_grid: np.ndarray, h0: float = 70., order: int = 64) -> dict:
        grid = np.asarray(omega_grid, dtype=float)
        if grid.ndim != 1 or len(grid) < 3 or not np.isfinite(grid).all() or np.any(np.diff(grid) <= 0):
            raise ValueError('omega_grid must be strictly increasing with >=3 entries')
        fits = [self.fit(float(om), h0, order) for om in grid]
        chi = np.array([f.chi2 for f in fits])
        idx = int(np.argmin(chi))
        return {'omega_grid':grid, 'chi2':chi, 'delta_chi2':chi-chi[idx],
                'best_omega_m':float(grid[idx]),'best_offset':fits[idx].offset,
                'best_offset_sigma':fits[idx].offset_sigma,
                'min_chi2':float(chi[idx])}


def quadrature_convergence(z: np.ndarray, omega_m: float,
                           orders: tuple[int,...] = (8,16,32,64,128)) -> dict[int,float]:
    """Maximum absolute distance-modulus change relative to finest order [mag]."""
    if len(orders) < 2 or any(o < 2 for o in orders) or sorted(set(orders)) != list(orders):
        raise ValueError('orders must be increasing and unique')
    reference = distance_modulus(z,omega_m,order=orders[-1])
    return {o:float(np.max(np.abs(distance_modulus(z,omega_m,order=o)-reference))) for o in orders}


def redshift_delete_one_bin(z: np.ndarray, mu: np.ndarray, sigma: np.ndarray,
                            omega_grid: np.ndarray, *, bins: int = 4,
                            intrinsic_scatter: float = 0.) -> list[dict]:
    """Redshift-quantile delete-one-bin profile; *diagonal-only* sensitivity.

    Refit nuisance offset for every subset. Results are robustness checks, not
    a jackknife covariance of cosmological parameters or a systematic budget.
    """
    z,mu,sigma = [np.asarray(v,dtype=float) for v in (z,mu,sigma)]
    if z.ndim != 1 or mu.shape != z.shape or sigma.shape != z.shape or bins < 2 or len(z) < bins*3:
        raise ValueError('insufficient or inconsistent data for redshift deletion')
    order = np.argsort(z,kind='stable')
    groups = np.array_split(order,bins)
    output=[]
    for k,deleted in enumerate(groups):
        keep=np.ones(len(z),dtype=bool)
        keep[deleted]=False
        prof=CovarianceProfiler(z[keep],mu[keep],covariance_matrix(sigma[keep],intrinsic_scatter))
        result=prof.grid_profile(omega_grid)
        output.append({'deleted_bin':k,'deleted_count':int(len(deleted)),
                       'redshift_min':float(np.min(z[deleted])),
                       'redshift_max':float(np.max(z[deleted])),
                       'remaining_count':int(keep.sum()),
                       'best_omega_m':result['best_omega_m'],
                       'min_chi2':result['min_chi2']})
    return output
