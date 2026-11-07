import math
import unittest
from hubble_robustness import luminosity_distance,distance_modulus,profile_offset

class TestHubble(unittest.TestCase):
    def test_de_sitter_analytic(self):
        for z in (.01,.5,2):
            self.assertAlmostEqual(luminosity_distance(z,0),299792.458/70*z*(1+z),places=8)
    def test_quadrature_convergence(self):
        a=luminosity_distance(1.8,.3,steps=16)
        b=luminosity_distance(1.8,.3,steps=32)
        ref=luminosity_distance(1.8,.3,steps=1024)
        self.assertLess(abs(b-ref),abs(a-ref)/10)
    def test_h0_degeneracy(self):
        zs=[.03,.2,.8]
        x=[distance_modulus(z,.3,70) for z in zs]
        y=[distance_modulus(z,.3,80) for z in zs]
        obs=[v+.4 for v in x]
        self.assertAlmostEqual(profile_offset(obs,x,[.1]*3)[1],profile_offset(obs,y,[.1]*3)[1],places=20)
    def test_offset_recovery(self):
        self.assertAlmostEqual(profile_offset([2,3,4],[1,2,3],[.1,.2,.3])[0],1)
    def test_bad_sigma(self):
        with self.assertRaises(ValueError): profile_offset([1],[1],[0])
if __name__=='__main__': unittest.main()
