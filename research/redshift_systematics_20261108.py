"""Low-z redshift and peculiar-velocity sensitivity for flat Lambda-CDM.

Synthetic diagnostics only: independent redshift perturbations and a shared
calibration floor are illustrative, not Pantheon+ covariance. H0 in km/s/Mpc,
velocity in km/s. No cosmological parameter inference. AI-assisted code.
"""
import math
import unittest

C_KMS=299792.458

def e_z(z, omega_m):
    if not (math.isfinite(z) and z>=0 and 0<=omega_m<=1):
        raise ValueError("Invalid cosmological input")
    return math.sqrt(omega_m*(1+z)**3 + 1-omega_m)

def luminosity_distance_mpc(z, h0=70., omega_m=0.3, n=400):
    if not (math.isfinite(h0) and h0>0 and isinstance(n,int) and n>=2 and n%2==0):
        raise ValueError("Invalid integration settings")
    if not (math.isfinite(z) and z>0):
        raise ValueError("z must be positive")
    step=z/n
    integ=1/e_z(0,omega_m)+1/e_z(z,omega_m)
    integ+=4*math.fsum(1/e_z(step*i,omega_m) for i in range(1,n,2))
    integ+=2*math.fsum(1/e_z(step*i,omega_m) for i in range(2,n,2))
    return (1+z)*C_KMS/h0 * step*integ/3

def distance_modulus(z, h0=70., omega_m=0.3):
    return 5*math.log10(luminosity_distance_mpc(z,h0,omega_m))+25

def peculiar_velocity_mu_sigma(z, velocity_sigma_kms, h0=70., omega_m=0.3):
    """First-order observed-z perturbation, dz=(1+z)*v/c.

    This is NOT a complete peculiar-velocity likelihood or flow correction.
    """
    if not (math.isfinite(velocity_sigma_kms) and velocity_sigma_kms>=0):
        raise ValueError("Invalid velocity dispersion")
    if not (math.isfinite(z) and z>0):
        raise ValueError("Invalid redshift")
    step=min(1e-5, z/100)
    derivative=(distance_modulus(z+step,h0,omega_m)-
                distance_modulus(z-step,h0,omega_m))/(2*step)
    return abs(derivative)*(1+z)*velocity_sigma_kms/C_KMS

def mean_uncertainty(independent_sigmas, shared_mag_sigma=0):
    """Inverse-variance weighted mean variance with rank-one shared floor."""
    if not independent_sigmas or not all(math.isfinite(s) and s>0 for s in independent_sigmas):
        raise ValueError("Independent sigmas must be finite and positive")
    if not math.isfinite(shared_mag_sigma) or shared_mag_sigma<0:
        raise ValueError("Invalid shared floor")
    return math.sqrt(1/math.fsum(1/s**2 for s in independent_sigmas)+shared_mag_sigma**2)

class SupernovaTests(unittest.TestCase):
    def test_low_z_distance(self):
        z=1e-5
        self.assertAlmostEqual(luminosity_distance_mpc(z)/(C_KMS*z/70),1,delta=2e-5)
    def test_velocity_scaling(self):
        a=peculiar_velocity_mu_sigma(.02,150)
        self.assertAlmostEqual(peculiar_velocity_mu_sigma(.02,300)/a,2)
    def test_low_z_approximation(self):
        z=.001
        approximate=5/math.log(10)*300/(C_KMS*z)
        self.assertAlmostEqual(peculiar_velocity_mu_sigma(z,300)/approximate,1,delta=.004)
    def test_shared_floor(self):
        self.assertAlmostEqual(mean_uncertainty([.1]*4,.02),math.hypot(.05,.02))
    def test_invalid(self):
        with self.assertRaises(ValueError): peculiar_velocity_mu_sigma(0,300)
        with self.assertRaises(ValueError): mean_uncertainty([.1,0])

if __name__=="__main__":
    unittest.main()
