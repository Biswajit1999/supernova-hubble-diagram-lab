"""Synthetic validation by default; optionally analyze repository's 180-row subset.

This is deliberately NOT a reproduction of the Pantheon+ full covariance likelihood.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from research.covariance_diagnostics import (distance_modulus,covariance_matrix,CovarianceProfiler,
    quadrature_convergence,redshift_delete_one_bin)


def main(output: Path, reference: Path | None = None):
    output.mkdir(parents=True,exist_ok=True)
    if reference is None:
        z=np.linspace(.02,1.4,64)
        rng=np.random.default_rng(20261019)
        sigma=np.full(len(z),.09)
        mu=distance_modulus(z,.31)+.12+rng.normal(0,sigma)
        source='synthetic seeded flat-LCDM fixture'
    else:
        data=json.loads(reference.read_text())
        rows=data['points']
        z=np.array([p['x'] for p in rows],dtype=float)
        mu=np.array([p['y'] for p in rows],dtype=float)
        sigma=np.array([p['y_err'] for p in rows],dtype=float)
        source='180-row diagonal-only display subset; not official Pantheon+ likelihood'
    grid=np.linspace(.05,1.,96)
    diagonal=CovarianceProfiler(z,mu,covariance_matrix(sigma, intrinsic_scatter=.1)).grid_profile(grid)
    # Hypothetical common-mode calibration: NOT an estimate of Pantheon+ systematics.
    u=np.full((len(z),1),.04)
    correlated=CovarianceProfiler(z,mu,covariance_matrix(sigma,intrinsic_scatter=.1,systematics=u)).grid_profile(grid)
    deletion=redshift_delete_one_bin(z,mu,sigma,grid,bins=4,intrinsic_scatter=.1)
    convergence=quadrature_convergence(z,.3)
    with (output/'profile.csv').open('w',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['omega_m','diagonal_delta_chi2','scenario_commonmode_delta_chi2'])
        for i,om in enumerate(grid):
            writer.writerow([om,diagonal['delta_chi2'][i],correlated['delta_chi2'][i]])
    summary={'source':source,'n':len(z),'diagonal_best_omega_m':diagonal['best_omega_m'],
             'scenario_commonmode_best_omega_m':correlated['best_omega_m'],
             'diagonal_offset_sigma':diagonal['best_offset_sigma'],
             'scenario_commonmode_offset_sigma':correlated['best_offset_sigma'],
             'redshift_delete_one_bin':deletion,'quadrature_max_abs_mag':convergence,
             'limitations':['No official Pantheon+ covariance, peculiar-velocity, calibration or repeated-CID model.',
                            '0.04 mag common-mode factor is hypothetical, not a measured systematic.',
                            'No H0 inference: free additive offset is exactly degenerate with H0.',
                            'Grid minima and redshift deletion are diagnostics, not confidence intervals.']}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path,default=None,help='Optional existing data/reference.json')
    parser.add_argument('--output',type=Path,default=Path('results/covariance_diagnostics'))
    args=parser.parse_args()
    main(args.output,args.reference)
