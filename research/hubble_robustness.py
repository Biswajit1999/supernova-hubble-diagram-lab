"""Flat-LCDM quadrature and profiled-magnitude diagnostics (diagonal errors only)."""
from __future__ import annotations
import math

C_KM_S = 299792.458

def luminosity_distance(z: float, omega_m: float, h0: float = 70., steps: int = 256) -> float:
    """Composite Simpson flat-LCDM luminosity distance, in Mpc."""
    if not all(math.isfinite(x) for x in (z,omega_m,h0)) or z <= 0 or not 0 <= omega_m <= 1 or h0 <= 0:
        raise ValueError('require z>0, 0<=omega_m<=1, h0>0 and finite inputs')
    if not isinstance(steps,int) or steps < 2 or steps % 2:
        raise ValueError('Simpson steps must be a positive even integer')
    h = z / steps
    def inv_e(x: float) -> float:
        return 1 / math.sqrt(omega_m * (1+x)**3 + (1-omega_m))
    integral = inv_e(0) + inv_e(z)
    for k in range(1,steps):
        integral += (4 if k%2 else 2)*inv_e(k*h)
    return (1+z)*C_KM_S/h0*integral*h/3

def distance_modulus(z: float, omega_m: float, h0: float = 70., steps: int = 256) -> float:
    return 5*math.log10(luminosity_distance(z,omega_m,h0,steps))+25

def profile_offset(observed: list[float], model: list[float], sigma: list[float]) -> tuple[float,float]:
    """Best additive magnitude offset and diagonal chi-square; no full covariance."""
    if not observed or len(observed)!=len(model) or len(model)!=len(sigma):
        raise ValueError('equal nonempty arrays required')
    if not all(math.isfinite(v) for row in (observed,model,sigma) for v in row) or any(s<=0 for s in sigma):
        raise ValueError('finite values and strictly positive errors required')
    weights=[1/(s*s) for s in sigma]
    delta=sum(w*(y-m) for w,y,m in zip(weights,observed,model))/sum(weights)
    chi2=sum(w*(y-m-delta)**2 for w,y,m in zip(weights,observed,model))
    return delta,chi2
