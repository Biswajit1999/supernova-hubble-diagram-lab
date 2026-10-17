"""Deterministic synthetic tests for independent supernova numerical diagnostics."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cosmology_robustness import (covariance_from_errors, distance_modulus, expansion_rate,
                                  profile_offset, profile_omega, redshift_bin_jackknife,
                                  redshift_cut_sensitivity)


def fixture():
    z = np.linspace(0.02, 1.2, 50)
    sigma = np.full(len(z), 0.09)
    mu = distance_modulus(z, 0.3, 70) + 0.17
    return z, mu, sigma


class CosmologyRobustnessTests(unittest.TestCase):
    def test_matter_dominated_analytic(self):
        z = np.array([0.02, 0.2, 1.2])
        integral = 2 * (1 - 1 / np.sqrt(1 + z))
        exact = 5 * np.log10((1 + z) * 299792.458 * integral / 70) + 25
        np.testing.assert_allclose(distance_modulus(z, 1.0), exact, atol=2e-12)

    def test_simpson_convergence(self):
        z = 1.5
        truth = distance_modulus(z, 0.3)
        e1 = abs(distance_modulus(z, 0.3, method="simpson", steps=8) - truth)
        e2 = abs(distance_modulus(z, 0.3, method="simpson", steps=16) - truth)
        self.assertLess(e2, e1 / 8)

    def test_h0_exact_shift(self):
        a = distance_modulus(0.7, 0.3, 70)
        b = distance_modulus(0.7, 0.3, 75)
        self.assertAlmostEqual(b - a, 5 * np.log10(70 / 75), places=12)

    def test_covariance_spd(self):
        z, _, sigma = fixture()
        cov = covariance_from_errors(z, sigma, 0.65, 0.2)
        np.linalg.cholesky(cov)
        np.testing.assert_allclose(np.diag(cov), sigma ** 2)

    def test_invalid_covariance(self):
        z, _, sigma = fixture()
        with self.assertRaises(ValueError):
            covariance_from_errors(z, sigma, correlation=1.0)

    def test_profile_zero_noise_recovery(self):
        z, mu, sigma = fixture()
        cov = np.diag(sigma ** 2)
        fit = profile_offset(z, mu, cov, 0.3)
        self.assertAlmostEqual(fit["offset"], 0.17, places=9)
        self.assertLess(fit["chi2"], 1e-18)

    def test_h0_offset_degeneracy(self):
        z, mu, sigma = fixture()
        cov = covariance_from_errors(z, sigma, 0.4, 0.1)
        a = profile_offset(z, mu, cov, 0.3, 70)
        b = profile_offset(z, mu, cov, 0.3, 75)
        self.assertAlmostEqual(a["chi2"], b["chi2"], places=11)
        self.assertAlmostEqual(b["offset"] - a["offset"], 5 * np.log10(75 / 70), places=11)

    def test_omega_recovery(self):
        z, mu, sigma = fixture()
        grid = np.linspace(0.1, 0.9, 41)
        fit = profile_omega(z, mu, np.diag(sigma ** 2), grid)
        self.assertAlmostEqual(fit["best_omega_m"], 0.3, places=12)
        self.assertAlmostEqual(min(fit["delta_chi2"]), 0, places=12)

    def test_cut_and_jackknife(self):
        z, mu, sigma = fixture()
        cov = np.diag(sigma ** 2)
        grid = np.linspace(0.1, 0.9, 41)
        cuts = redshift_cut_sensitivity(z, mu, cov, (0.01, 0.2, 0.5), grid)
        self.assertTrue(all(abs(r["best_omega_m"] - 0.3) < 1e-12 for r in cuts))
        jk = redshift_bin_jackknife(z, mu, cov, 5, grid)
        self.assertEqual(len(jk["bins"]), 5)
        self.assertTrue(all(abs(r["delta_from_full"]) < 1e-12 for r in jk["bins"]))

    def test_invalid_distance_inputs(self):
        with self.assertRaises(ValueError):
            distance_modulus(-0.1, 0.3)
        with self.assertRaises(ValueError):
            expansion_rate(0.1, 1.5)


if __name__ == "__main__":
    unittest.main()
