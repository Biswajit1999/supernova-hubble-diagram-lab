import numpy as np
import pytest
from research.covariance_diagnostics import (luminosity_distance,distance_modulus,covariance_matrix,
    CovarianceProfiler,quadrature_convergence,redshift_delete_one_bin)


def fixture():
    z=np.linspace(.03,1.1,45)
    mu=distance_modulus(z,.31)+.16
    sigma=np.full(len(z),.10)
    return z,mu,sigma


def test_hubble_scaling():
    z,_,_=fixture()
    a=distance_modulus(z,.3,70)
    b=distance_modulus(z,.3,80)
    np.testing.assert_allclose(b-a,5*np.log10(70/80),atol=1e-12)


def test_omega_zero_analytic_distance():
    z=np.array([.1,.5,1.5])
    np.testing.assert_allclose(luminosity_distance(z,0),299792.458/70*z*(1+z),rtol=1e-13)


def test_omega_one_analytic_distance():
    z=np.array([.1,.5,1.5])
    expected=(1+z)*(299792.458/70)*2*(1-1/np.sqrt(1+z))
    np.testing.assert_allclose(luminosity_distance(z,1),expected,rtol=1e-12)


def test_quadrature_converges():
    errors=quadrature_convergence(np.linspace(.01,2.3,40),.3)
    assert errors[8]<1e-5
    assert errors[32]<1e-10
    assert errors[128]==0


def test_diagonal_covariance_matches_weighted_offset():
    z,mu,s=fixture()
    mu=mu+np.sin(z*8)*.04
    prof=CovarianceProfiler(z,mu,covariance_matrix(s))
    result=prof.fit(.31)
    resid=mu-distance_modulus(z,.31)
    assert result.offset==pytest.approx(np.average(resid,weights=1/s**2))
    assert result.chi2==pytest.approx(np.sum(((resid-result.offset)/s)**2))
    assert result.offset_sigma==pytest.approx(.1/np.sqrt(len(z)))


def test_correlated_common_mode_increases_offset_uncertainty():
    z,mu,s=fixture()
    diag=CovarianceProfiler(z,mu,covariance_matrix(s)).fit(.31)
    common=np.full((len(z),1),.08)
    corr=CovarianceProfiler(z,mu,covariance_matrix(s,systematics=common)).fit(.31)
    assert corr.offset_sigma>diag.offset_sigma
    assert corr.offset==pytest.approx(diag.offset,abs=1e-12)
    assert corr.chi2==pytest.approx(diag.chi2,abs=1e-12)


def test_h0_profile_invariance():
    z,mu,s=fixture()
    p=CovarianceProfiler(z,mu,covariance_matrix(s))
    a=p.fit(.3,65)
    b=p.fit(.3,80)
    assert a.chi2==pytest.approx(b.chi2,abs=1e-10)
    assert b.offset-a.offset==pytest.approx(5*np.log10(80/65),abs=1e-11)


def test_injected_omega_recovered_grid():
    z,mu,s=fixture()
    p=CovarianceProfiler(z,mu,covariance_matrix(s))
    result=p.grid_profile(np.linspace(.15,.5,71))
    assert result['best_omega_m']==pytest.approx(.31,abs=.005)
    assert result['min_chi2']<1e-18
    assert np.min(result['delta_chi2'])==0


def test_whitened_residual_chi2():
    z,mu,s=fixture()
    p=CovarianceProfiler(z,mu+np.sin(z*8)*.05,covariance_matrix(s))
    fit=p.fit(.31)
    assert fit.chi2==pytest.approx(float(fit.whitened_residuals@fit.whitened_residuals))


def test_delete_bin_recovers_injected_parameter():
    z,mu,s=fixture()
    out=redshift_delete_one_bin(z,mu,s,np.linspace(.2,.4,41),bins=3)
    assert len(out)==3
    assert sum(x['deleted_count'] for x in out)==len(z)
    assert all(x['best_omega_m']==pytest.approx(.31,abs=.005) for x in out)


def test_non_spd_covariance_rejected():
    z,mu,s=fixture()
    bad=np.eye(len(z));bad[0,0]=-1
    with pytest.raises(ValueError,match='positive definite'): CovarianceProfiler(z,mu,bad)


@pytest.mark.parametrize('invalid',[0,-1,np.nan])
def test_invalid_sigma(invalid):
    with pytest.raises(ValueError): covariance_matrix([.1,invalid])


def test_bad_redshift_rejected():
    with pytest.raises(ValueError): luminosity_distance(np.array([0,.1]),.3)
