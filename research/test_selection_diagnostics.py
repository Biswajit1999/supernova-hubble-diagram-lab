import unittest
import numpy as np
from selection_diagnostics import profile_offset, covariance_with_common_floor, redshift_cut_stability

class Tests(unittest.TestCase):
    def test_exact_offset(self):
        a, err, chi = profile_offset([2., 2., 2.], np.eye(3))
        self.assertAlmostEqual(a, 2.)
        self.assertAlmostEqual(err, 1/np.sqrt(3))
        self.assertAlmostEqual(chi, 0.)
    def test_common_floor_not_reduced(self):
        c = covariance_with_common_floor([1.,1.,1.,1.], .5)
        _, err, _ = profile_offset(np.ones(4), c)
        self.assertAlmostEqual(err, np.sqrt(.25+.25))
    def test_cut(self):
        rows = redshift_cut_stability([.01,.1,.2], [1,2,3], [1,1,1], [.0,.1,.3])
        self.assertAlmostEqual(rows[0][2], 2.)
        self.assertAlmostEqual(rows[1][2], 2.5)
        self.assertEqual(rows[2][1], 0)
    def test_non_spd(self):
        with self.assertRaises(np.linalg.LinAlgError):
            profile_offset([1,2], [[1,2],[2,1]])
    def test_rejects_asymmetric_covariance(self):
        with self.assertRaisesRegex(ValueError, "covariance must be symmetric"):
            profile_offset([1, 2], [[1, 0.8], [0.1, 1]])
if __name__ == '__main__': unittest.main()
