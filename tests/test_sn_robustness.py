"""Independent numerical regression tests; no network or optional packages."""
import math
import unittest

from scripts import sn_robustness as sn


class SupernovaRobustnessTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"x": 0.05, "y": 36.8, "y_err": 0.12},
            {"x": 0.15, "y": 39.3, "y_err": 0.13},
            {"x": 0.35, "y": 41.4, "y_err": 0.14},
            {"x": 0.7, "y": 43.1, "y_err": 0.17},
        ]

    def test_diagonal_inverse(self):
        result = sn.inverse_covariance_product([2, 6], [1, 2], [1, 2], 0)
        self.assertEqual(result, [2.0, 1.5])

    def test_rank_one_matches_exact_two_by_two_inverse(self):
        result = sn.inverse_covariance_product([2, 0], [1, 1], [1, 1], 1)
        self.assertAlmostEqual(result[0], 4 / 3)
        self.assertAlmostEqual(result[1], -2 / 3)

    def test_constant_systematic_is_absorbed_by_profiled_offset(self):
        a = sn.profile_offset(self.rows, 0.3, tau=0, shape_mode="constant")
        b = sn.profile_offset(self.rows, 0.3, tau=0.5, shape_mode="constant")
        self.assertAlmostEqual(a["chi2"], b["chi2"], places=8)

    def test_hubble_constant_degeneracy(self):
        a = sn.profile_offset(self.rows, 0.3, h0=70)
        b = sn.profile_offset(self.rows, 0.3, h0=75)
        self.assertAlmostEqual(a["chi2"], b["chi2"], places=8)
        self.assertAlmostEqual(
            b["offset_mag"] - a["offset_mag"], 5 * math.log10(75 / 70),
            places=8,
        )

    def test_rejects_invalid_covariance(self):
        with self.assertRaises(ValueError):
            sn.inverse_covariance_product([1], [0], [1], 0.1)
        with self.assertRaises(ValueError):
            sn.inverse_covariance_product([1], [1], [1], -0.1)

    def test_real_reference_replays_on_sparse_subsample(self):
        rows = sn.load_points(sn.ROOT / "data" / "reference.json")
        self.assertEqual(len(rows), 180)
        fit = sn.grid_fit(rows[::9])
        self.assertEqual(fit["n"], 20)
        self.assertTrue(math.isfinite(fit["chi2"]))
        self.assertTrue(0.05 <= fit["omega_m"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
