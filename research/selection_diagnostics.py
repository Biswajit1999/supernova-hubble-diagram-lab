"""Conditional SN Hubble-diagram diagnostics; no catalogue likelihood claims."""
import numpy as np

def profile_offset(residual, covariance):
    """Profile additive magnitude offset with full SPD covariance."""
    y = np.asarray(residual, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if y.ndim != 1 or not len(y) or c.shape != (len(y), len(y)) or not np.all(np.isfinite(y)) or not np.all(np.isfinite(c)):
        raise ValueError('invalid residual or covariance')
    l = np.linalg.cholesky(c)
    wy = np.linalg.solve(l, y)
    w1 = np.linalg.solve(l, np.ones_like(y))
    den = w1 @ w1
    offset = (w1 @ wy) / den
    chi2 = np.sum((wy - offset * w1)**2)
    return float(offset), float(den**-0.5), float(chi2)

def covariance_with_common_floor(sigma, common_mag):
    """Independent errors plus a fully shared zero-point uncertainty."""
    s = np.asarray(sigma, dtype=float)
    if s.ndim != 1 or not len(s) or not np.all(np.isfinite(s)) or np.any(s <= 0) or not np.isfinite(common_mag) or common_mag < 0:
        raise ValueError('invalid errors')
    return np.diag(s*s) + common_mag**2 * np.ones((len(s), len(s)))

def redshift_cut_stability(z, residual, sigma, cuts):
    """Profile offsets on nested redshift cuts; diagonal-only sensitivity."""
    z, y, s = (np.asarray(a, dtype=float) for a in (z, residual, sigma))
    if z.ndim != 1 or y.shape != z.shape or s.shape != z.shape or not np.all(np.isfinite(z)) or not np.all(np.isfinite(y)) or not np.all(np.isfinite(s)) or np.any(s <= 0):
        raise ValueError('invalid inputs')
    out = []
    for cut in cuts:
        if not np.isfinite(cut):
            raise ValueError('invalid cut')
        keep = z >= cut
        if not keep.any():
            out.append((float(cut), 0, float('nan'), float('nan')))
            continue
        w = 1/s[keep]**2
        mu = np.sum(w*y[keep])/np.sum(w)
        out.append((float(cut), int(keep.sum()), float(mu), float(np.sqrt(1/w.sum()))))
    return out
