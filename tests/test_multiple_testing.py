from __future__ import annotations
import numpy as np
import pytest
from anomaly_audit.core import multiple_testing as mt

P=np.array([0.001,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09])

def test_bonferroni_count():
    # reject p<=0.05/10=0.005->only 0.001
    res=mt.bonferroni(P,alpha=0.05)
    assert res.n_significant==1

def test_holm_count():
    # step-down stops after the first failure: only p(1)=0.001<=0.05/10
    res=mt.holm(P,alpha=0.05)
    assert res.n_significant==1

def test_benjamini_hochberg_count():
    # largest k with p_(k)<=k/10*0.05: k=2 (0.01<=0.01)->reject 2 smallest
    res=mt.benjamini_hochberg(P,alpha=0.05)
    assert res.n_significant==2

def test_power_ordering():
    bonf=mt.bonferroni(P).n_significant
    holm=mt.holm(P).n_significant
    bh=mt.benjamini_hochberg(P).n_significant
    assert bh>=holm>=bonf

def test_pvalue_tstat_roundtrip():
    t=np.array([2.0,3.0,1.5])
    p=mt.two_sided_pvalue_from_t(t)
    t_back=mt.t_from_two_sided_pvalue(p)
    assert np.allclose(t_back,t,atol=1e-6)

def test_adjusted_pvalues_monotone():
    res=mt.benjamini_hochberg(P)
    q=np.array(res.adjusted_pvalues)
    order=np.argsort(P)
    assert np.all(np.diff(q[order])>=-1e-12)  # non-decreasing in p

def test_haircut_between_zero_and_one():
    tstats=np.array([5.0,3.0,2.1,1.0,0.5])
    p=mt.two_sided_pvalue_from_t(tstats)
    bh=mt.benjamini_hochberg(p)
    hc=mt.haircut_sharpe(tstats,bh)
    frac=np.array(hc.haircut_fraction)
    assert np.all((frac>=0) & (frac<=1))