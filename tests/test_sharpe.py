from __future__ import annotations
import numpy as np
import pytest
from anomaly_audit.core import sharpe,metrics

def test_sharpe_ratio_known_value():
    # constant-mean series: SR=mean/std*sqrt(12)
    rng=np.random.default_rng(0)
    r=rng.normal(0.01,0.04,100000)
    sr=metrics.sharpe_ratio(r,12)
    expected=0.01/0.04*np.sqrt(12)
    assert sr==pytest.approx(expected,rel=0.05)

def test_psr_half_at_zero_sharpe():
    psr=sharpe.probabilistic_sharpe_ratio(sr=0.0,n=240,skew=0.0,kurt=3.0)
    assert psr==pytest.approx(0.5,abs=1e-9)

def test_psr_increases_with_sharpe():
    a=sharpe.probabilistic_sharpe_ratio(0.10,240,0.0,3.0)
    b=sharpe.probabilistic_sharpe_ratio(0.20,240,0.0,3.0)
    assert b>a

def test_psr_penalizes_negative_skew_and_fat_tails():
    base=sharpe.probabilistic_sharpe_ratio(0.15,240,0.0,3.0)
    skewed=sharpe.probabilistic_sharpe_ratio(0.15,240,-1.0,8.0)
    assert skewed<base

def test_expected_max_sharpe_increases_with_trials():
    v=0.02
    assert sharpe.expected_max_sharpe(v,100)>sharpe.expected_max_sharpe(v,10)
    assert sharpe.expected_max_sharpe(v,2)>=0.0

def test_deflated_below_probabilistic():
    psr=sharpe.probabilistic_sharpe_ratio(0.2,240,0.0,3.0,sr_benchmark=0.0)
    dsr=sharpe.deflated_sharpe_ratio(0.2,240,0.0,3.0,n_trials=100,sr_variance=0.02)
    assert dsr<psr

def test_min_track_record_length_infinite_when_below_benchmark():
    assert sharpe.min_track_record_length(0.0,0.0,3.0,sr_benchmark=0.1)==np.inf
    finite=sharpe.min_track_record_length(0.3,0.0,3.0,sr_benchmark=0.0)
    assert np.isfinite(finite) and finite>1

def test_sharpe_report_fields():
    rng=np.random.default_rng(1)
    r=rng.normal(0.006,0.03,360)
    rep=sharpe.sharpe_report(r,n_trials=50,sr_variance=0.01)
    assert rep.n==360
    assert 0.0<=rep.psr<=1.0
    assert 0.0<=rep.dsr<=1.0
    assert rep.dsr<=rep.psr+1e-9