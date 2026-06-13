from __future__ import annotations
import numpy as np
import pytest
from anomaly_audit.core import pbo

def test_placebo_pbo_near_half():
    rng=np.random.default_rng(123)
    vals=[]
    for _ in range(5):
        noise=rng.standard_normal((480,60))*0.04
        vals.append(pbo.compute_pbo(noise,n_splits=14).pbo)
    assert np.mean(vals)==pytest.approx(0.5,abs=0.08)

def test_persistent_signal_low_pbo():
    rng=np.random.default_rng(7)
    mat=rng.standard_normal((480,40))*0.04
    # make column 0 genuinely good in every period
    mat[:,0]+=0.02
    res=pbo.compute_pbo(mat,n_splits=14)
    assert res.pbo<0.2

def test_pbo_requires_even_splits():
    rng=np.random.default_rng(0)
    mat=rng.standard_normal((100,10))*0.04
    with pytest.raises(ValueError):
        pbo.compute_pbo(mat,n_splits=7)

def test_pbo_combination_count():
    rng=np.random.default_rng(0)
    mat=rng.standard_normal((200,12))*0.04
    res=pbo.compute_pbo(mat,n_splits=8)
    assert res.n_combinations==70 # C(8,4)=70
    assert 0.0<=res.pbo<=1.0
