from __future__ import annotations
import datetime as _dt
from dataclasses import dataclass,field
from typing import Any
import numpy as np
import pandas as pd
from scipy.stats import norm
from anomaly_audit.config import Config
from anomaly_audit.core import decay as decay_mod
from anomaly_audit.core import metrics
from anomaly_audit.core import multiple_testing as mt
from anomaly_audit.core import pbo as pbo_mod
from anomaly_audit.core import regimes as regime_core
from anomaly_audit.core import sharpe as sharpe_mod
from anomaly_audit.data.dataset import Dataset

@dataclass
class AuditResults:
    meta: dict[str,Any]
    summary: dict[str,Any]
    funnel: list[dict[str,Any]]
    anomalies: list[dict[str,Any]]
    pbo: dict[str,Any]
    multiple_testing: dict[str,Any]
    regime_order: list[str]
    decay_distribution: list[float]
    category_summary: list[dict[str,Any]]

    def to_dict(self)->dict[str,Any]:
        return {
            "meta": self.meta,
            "summary": self.summary,
            "funnel": self.funnel,
            "anomalies": self.anomalies,
            "pbo": self.pbo,
            "multiple_testing": self.multiple_testing,
            "regime_order": self.regime_order,
            "decay_distribution": self.decay_distribution,
            "category_summary": self.category_summary,
        }

def _verdict(
    oos_sharpe: float,oos_t: float,dsr_oos:
    float,bh_sig:bool,regime_verdict: str,dsr_threshold: float,)->str:
    if not np.isfinite(oos_sharpe) or oos_sharpe<=0 or oos_t<=0:
        return "Dead"
    survives_stats=(dsr_oos>=dsr_threshold) and bh_sig
    if survives_stats and regime_verdict=="Robust":
        return "Robust"
    if regime_verdict in ("Robust","Regime-dependent") and oos_t>=2.0:
        return "Regime-dependent"
    return "Decayed"

def run_audit(ds: Dataset,cfg: Config,verbose: bool=True)->AuditResults:
    def _log(msg: str)->None:
        if verbose:
            print(msg)

    stats_cfg=cfg.statistics
    ppy=int(stats_cfg["annualization"])
    dsr_threshold=float(stats_cfg["dsr_threshold"])
    naive_t=float(stats_cfg["sharpe_significance"])
    fdr_alpha=float(stats_cfg["fdr_alpha"])
    min_oos=int(cfg.data["min_oos_months"])
    panel=ds.panel
    names=list(panel.columns)
    n_anom=len(names)
    full_mat=panel.to_numpy()

    sr_variance=sharpe_mod.cross_sectional_sr_variance(full_mat)
    _log(f"[audit] {n_anom} anomalies | cross-sectional SR variance V={sr_variance:.5f}")

    regimes_df=regime_core.build_regimes(ds.macro,cfg.regimes)
    membership=regime_core.regime_membership(regimes_df)
    regime_order=list(membership.keys())
    robust_min=int(cfg.regimes["robust_min_partitions"])
    vol_labels=cfg.regimes["vol_tercile_labels"]
    rate_labels=cfg.regimes["rate_labels"]
    break_labels=cfg.regimes["break_labels"]
    partitions=[
        ("Volatility",vol_labels[0],vol_labels[-1]),
        ("Rates",rate_labels[0],rate_labels[1]),
        ("Microstructure",break_labels[0],break_labels[1]),
    ]

    _log("[audit] running CSCV/PBO ...")
    n_splits=int(cfg.pbo["n_splits"])
    pbo_res=pbo_mod.compute_pbo(full_mat,n_splits=n_splits)
    _log(f"[audit] PBO={pbo_res.pbo:.3f} over {pbo_res.n_combinations} splits")

    placebo_rng=np.random.default_rng(cfg.seed+777)
    placebo_vals=[]
    for _ in range(5):
        noise=placebo_rng.standard_normal(full_mat.shape)*0.04
        placebo_vals.append(pbo_mod.compute_pbo(noise,n_splits=n_splits).pbo)
    pbo_placebo_val=float(np.mean(placebo_vals))
    _log(f"[audit] placebo PBO={pbo_placebo_val:.3f} (should be ~0.50)")

    date_index=[str(p) for p in panel.index]  # 'YYYY-MM'
    records: list[dict[str,Any]]=[]
    oos_tstats=np.full(n_anom,np.nan)

    for j,name in enumerate(names):
        series=panel[name]
        r=series.to_numpy()
        m=ds.meta.loc[name]
        pub_year=int(m["pub_year"])

        full_rep=sharpe_mod.sharpe_report(r,n_anom,sr_variance,ppy)
        dres=decay_mod.analyze_decay(series,pub_year,ppy)
        _,oos_r=decay_mod.split_is_oos(series,pub_year)
        is_r,_=decay_mod.split_is_oos(series,pub_year)
        oos_rep=sharpe_mod.sharpe_report(oos_r,n_anom,sr_variance,ppy)
        is_rep=sharpe_mod.sharpe_report(is_r,n_anom,sr_variance,ppy)
        oos_t=dres.oos_tstat
        oos_tstats[j]=oos_t
        oos_pval=float(norm.sf(oos_t)) if np.isfinite(oos_t) else 1.0
        rverd=regime_core.conditional_performance(
            series,membership,partitions,sig_t=naive_t,
            robust_min_partitions=robust_min,periods_per_year=ppy,
        )
        eq=metrics.cumulative_log_equity(r)
        pub_idx=int(np.searchsorted(np.array([int(s[:4]) for s in date_index]),pub_year+1))

        rec={
            "name": name,
            "category": str(m["category"]),
            "pub_year": pub_year,
            "orig_tstat": _f(m.get("orig_tstat",np.nan)),
            "turnover": _f(m.get("turnover",np.nan)),
            "audit_label": str(m["audit_label"]) if "audit_label" in ds.meta.columns else "",
            "home_regime": str(m.get("home_regime","")) if "home_regime" in ds.meta.columns else "",
            
            "sharpe_full": _f(full_rep.sharpe_annual),
            "tstat_full": _f(full_rep.t_stat),
            "skew": _f(full_rep.skew),
            "kurtosis": _f(full_rep.kurt),
            "max_drawdown": _f(metrics.max_drawdown(r)),
            "n_months": int(np.isfinite(r).sum()),
            "psr_full": _f(full_rep.psr),
            "dsr_full": _f(full_rep.dsr),
            "min_trl": _f(full_rep.min_track_record_length),
            "expected_max_sr": _f(full_rep.expected_max_sr_periodic*np.sqrt(ppy)),
            
            "is_sharpe": _f(dres.is_sharpe),
            "oos_sharpe": _f(dres.oos_sharpe),
            "is_tstat": _f(dres.is_tstat),
            "oos_tstat": _f(dres.oos_tstat),
            "decay_ratio": _f(dres.decay_ratio),
            "n_is": dres.n_is,
            "n_oos": dres.n_oos,
            "dsr_is": _f(is_rep.dsr),
            "dsr_oos": _f(oos_rep.dsr),
            "oos_pvalue": oos_pval,
            
            "regime_verdict": rverd.verdict,
            "n_regimes_significant": rverd.n_regimes_significant,
            "n_regimes_total": rverd.n_regimes_total,
            "n_partitions_spanned": rverd.n_partitions_spanned,
            "spanned_axes": rverd.spanned_axes,
            "regime_sharpes": {
                reg: _f(st["sharpe"]) for reg,st in rverd.per_regime.items()
            },
            "regime_significant": {
                reg: bool(st["significant"]) for reg,st in rverd.per_regime.items()
            },
            
            "equity_curve": [round(float(x),4) for x in eq],
            "pub_index": pub_idx,
        }
        records.append(rec)

    pvals=np.array([rec["oos_pvalue"] for rec in records])
    bh=mt.benjamini_hochberg(pvals,alpha=fdr_alpha)
    bonf=mt.bonferroni(pvals,alpha=fdr_alpha)
    holm=mt.holm(pvals,alpha=fdr_alpha)
    haircut=mt.haircut_sharpe(np.nan_to_num(oos_tstats,nan=0.0),bh,naive_t_hurdle=naive_t)

    for j,rec in enumerate(records):
        rec["bh_qvalue"]=_f(bh.adjusted_pvalues[j])
        rec["bh_significant"]=bool(bh.rejected[j]) and rec["oos_sharpe"] is not None and rec["oos_sharpe"]>0
        rec["bonferroni_significant"]=bool(bonf.rejected[j]) and rec["oos_sharpe"] is not None and rec["oos_sharpe"]>0
        rec["haircut_fraction"]=_f(haircut.haircut_fraction[j])
        rec["verdict"]=_verdict(
            rec["oos_sharpe"] if rec["oos_sharpe"] is not None else float("nan"),
            rec["oos_tstat"] if rec["oos_tstat"] is not None else float("nan"),
            rec["dsr_oos"] if rec["dsr_oos"] is not None else 0.0,
            rec["bh_significant"],
            rec["regime_verdict"],
            dsr_threshold,
        )

    funnel=_build_funnel(records,naive_t,dsr_threshold,robust_min)
    summary=_build_summary(records,pbo_res,bh,ds,min_oos)
    category_summary=_build_category_summary(records)
    multiple_testing={
        "fdr_alpha": fdr_alpha,
        "naive_t_hurdle": naive_t,
        "n_naive_significant": int(np.sum([
            (r["oos_tstat"] or -9)>=naive_t for r in records
        ])),
        "bh": {
            "n_significant": bh.n_significant,
            "cutoff_pvalue": _f(bh.cutoff_pvalue),
            "implied_t_hurdle": _f(bh.implied_t_hurdle),
        },
        "bonferroni": {
            "n_significant": bonf.n_significant,
            "implied_t_hurdle": _f(bonf.implied_t_hurdle),
        },
        "holm": {
            "n_significant": holm.n_significant,
            "implied_t_hurdle": _f(holm.implied_t_hurdle),
        },
        "haircut": {
            "median_haircut": _f(haircut.median_haircut),
            "adjusted_t_hurdle": _f(haircut.adjusted_t_hurdle),
        },
    }

    logits=np.array(pbo_res.logits)
    hist,edges=np.histogram(logits,bins=25)
    pbo_block={
        "pbo": _f(pbo_res.pbo),
        "pbo_placebo": _f(pbo_placebo_val),
        "n_combinations": pbo_res.n_combinations,
        "n_splits": pbo_res.n_splits,
        "prob_oos_loss": _f(pbo_res.prob_oos_loss),
        "perf_degradation_slope": _f(pbo_res.perf_degradation_slope),
        "logit_hist": {
            "counts": [int(c) for c in hist],
            "edges": [round(float(e),3) for e in edges],
        },
        "scatter": {
            "is": [round(float(x),4) for x in pbo_res.is_perf_selected[:2000]],
            "oos": [round(float(x),4) for x in pbo_res.oos_perf_selected[:2000]],
        },
    }

    decay_distribution=[
        r["decay_ratio"] for r in records
        if r["decay_ratio"] is not None and np.isfinite(r["decay_ratio"])
    ]

    meta={
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "data_source": ds.source,
        "has_ground_truth": ds.has_ground_truth,
        "n_anomalies": n_anom,
        "n_trials": n_anom,
        "sample_start": date_index[0],
        "sample_end": date_index[-1],
        "n_months": len(date_index),
        "seed": cfg.seed,
        "sr_cross_sectional_variance": _f(sr_variance),
        "dsr_threshold": dsr_threshold,
        "naive_t_hurdle": naive_t,
        "fdr_alpha": fdr_alpha,
        "dates": date_index,
        "regime_order": regime_order,
    }

    return AuditResults(
        meta=meta,summary=summary,funnel=funnel,anomalies=records,
        pbo=pbo_block,multiple_testing=multiple_testing,regime_order=regime_order,
        decay_distribution=decay_distribution,category_summary=category_summary,
    )

# _f: help convert to float or None..
def _f(x)->float | None:
    try:
        xf=float(x)
    except (TypeError,ValueError):
        return None
    if not np.isfinite(xf):
        return None
    return xf

# _build_funnel: build survival funnel..
def _build_funnel(records,naive_t,dsr_threshold,robust_min)->list[dict]:
    n=len(records)
    passes_oos_pos=np.array([(r["oos_sharpe"] or -9)>0 for r in records])
    passes_t2=np.array([(r["oos_tstat"] or -9)>=naive_t for r in records])
    passes_bh=np.array([r["bh_significant"] for r in records])
    passes_regime=np.array([r["regime_verdict"]=="Robust" for r in records])
    passes_dsr=np.array([(r["dsr_oos"] or 0)>=dsr_threshold for r in records])

    c1=passes_oos_pos
    c2=c1 & passes_t2
    c3=c2 & passes_bh
    c4=c3 & passes_regime
    c5=c4 & passes_dsr

    stages=[
        ("Published",n,"All anomalies entering the audit"),
        ("OOS Sharpe>0",int(c1.sum()),"Edge still positive after the publication date"),
        ("OOS t>2.0 (naive)",int(c2.sum()),"Clears the naive significance bar"),
        ("Survives BH-FDR",int(c3.sum()),"Significant after Benjamini-Hochberg multiple-testing control"),
        ("Regime-robust",int(c4.sum()),f"Significant on both sides of>={robust_min} macro axes"),
        ("Deflated-Sharpe significant",int(c5.sum()),f"P[true SR>0]>={dsr_threshold:g} after deflating for {n} trials"),
    ]
    return [
        {"stage": s,"count": c,"pct": round(100*c/n,1),"desc": d}
        for s,c,d in stages
    ]

# _build_summary: build summary stats..
def _build_summary(records,pbo_res,bh,ds: Dataset,min_oos)->dict:
    decays=[r["decay_ratio"] for r in records
              if r["decay_ratio"] is not None and np.isfinite(r["decay_ratio"])]
    verdicts=pd.Series([r["verdict"] for r in records])
    n=len(records)
    out={
        "median_decay_ratio": _f(np.median(decays)) if decays else None,
        "mean_decay_ratio": _f(np.mean(decays)) if decays else None,
        "pct_decayed": _f(100*np.mean([(r["decay_ratio"] or 1)<0.5 for r in records])),
        "pbo": _f(pbo_res.pbo),
        "n_robust": int((verdicts=="Robust").sum()),
        "n_regime_dependent": int((verdicts=="Regime-dependent").sum()),
        "n_decayed": int((verdicts=="Decayed").sum()),
        "n_dead": int((verdicts=="Dead").sum()),
        "pct_survive_naive": _f(100*np.mean([(r["oos_tstat"] or -9)>=2.0 for r in records])),
        "pct_survive_bh": _f(100*bh.n_significant/n),
        "verdict_counts": verdicts.value_counts().to_dict(),
    }
    # if we know the ground truth,score the audit's recovery of it
    if ds.has_ground_truth:
        gt=pd.Series([r["audit_label"] for r in records])
        out["ground_truth_counts"]=gt.value_counts().to_dict()
    return out

# _build_category_summary: build category summary
def _build_category_summary(records)->list[dict]:
    df=pd.DataFrame(records)
    rows=[]
    for cat,g in df.groupby("category"):
        rows.append({
            "category": cat,
            "n": int(len(g)),
            "median_oos_sharpe": _f(g["oos_sharpe"].median()),
            "median_decay": _f(g["decay_ratio"].median()),
            "n_robust": int((g["verdict"]=="Robust").sum()),
            "pct_survive_bh": _f(100*g["bh_significant"].mean()),
        })
    return sorted(rows,key=lambda r: -r["n"])