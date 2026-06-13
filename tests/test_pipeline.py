from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from anomaly_audit.config import load_config
from anomaly_audit.core import decay
from anomaly_audit.data import synthetic
from anomaly_audit.pipeline import run_audit

@pytest.fixture(scope="module")
def cfg():
    c=load_config()
    c.raw["data"]["source"]="synthetic"
    c.raw["data"]["n_anomalies"]=60  # smaller for speed
    return c

def test_split_is_oos():
    idx=pd.period_range("2000-01","2004-12",freq="M")
    s=pd.Series(np.arange(len(idx),dtype=float),index=idx)
    is_r,oos_r=decay.split_is_oos(s,pub_year=2002)
    assert len(is_r)==36   # 2000-2002 inclusive
    assert len(oos_r)==24  # 2003-2004

def test_synthetic_reproducible(cfg):
    a=synthetic.generate(cfg).panel.to_numpy()
    b=synthetic.generate(cfg).panel.to_numpy()
    assert np.array_equal(a,b)  # same seed->identical

def test_audit_funnel_is_monotone(cfg):
    ds=synthetic.generate(cfg)
    res=run_audit(ds,cfg,verbose=False)
    counts=[f["count"] for f in res.funnel]
    assert counts[0]==ds.n_anomalies
    assert all(counts[i]>=counts[i+1] for i in range(len(counts)-1))

def test_audit_recovers_ground_truth(cfg):
    ds=synthetic.generate(cfg)
    res=run_audit(ds,cfg,verbose=False)
    df=pd.DataFrame(res.anomalies)
    false_robust=df[(df["audit_label"]=="false") & (df["verdict"]=="Robust")]
    assert len(false_robust)==0
    robust=df[df["audit_label"]=="robust"]
    survived=robust[robust["verdict"].isin(["Robust","Regime-dependent"])]
    assert len(survived)/max(len(robust),1)>0.6

def test_results_json_serializable(cfg):
    import json
    from anomaly_audit.report.build_report import _sanitize
    ds=synthetic.generate(cfg)
    res=run_audit(ds,cfg,verbose=False)
    payload=_sanitize(res.to_dict())
    json.dumps(payload)  # must not raise