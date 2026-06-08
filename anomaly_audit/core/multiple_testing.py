from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
from scipy.stats import norm

def two_sided_pvalue_from_t(t: np.ndarray,dof: int | None=None)->np.ndarray:
    t=np.abs(np.asarray(t,dtype=float))
    if dof is None:
        return 2.0*norm.sf(t)
    from scipy.stats import t as tdist
    return 2.0*tdist.sf(t,df=dof)

def t_from_two_sided_pvalue(p: np.ndarray)->np.ndarray:
    p=np.clip(np.asarray(p,dtype=float),1e-300,1.0)
    return norm.ppf(1.0-p/2.0)

@dataclass
class CorrectionResult:
    method: str
    alpha: float
    n_tests: int
    n_significant: int
    rejected: list[bool]
    adjusted_pvalues: list[float]
    cutoff_pvalue: float
    implied_t_hurdle: float

    def as_dict(self)->dict:
        return asdict(self)

def _finalize(method,alpha,pvals,rejected,adj):
    rejected=np.asarray(rejected,dtype=bool)
    adj=np.asarray(adj,dtype=float)
    n_sig=int(rejected.sum())
    if n_sig>0:
        cutoff=float(np.max(np.asarray(pvals)[rejected]))
        implied_t=float(t_from_two_sided_pvalue(np.array([cutoff]))[0])
    else:
        cutoff=float("nan")
        implied_t=float("nan")
    return CorrectionResult(
        method=method,
        alpha=alpha,
        n_tests=len(pvals),
        n_significant=n_sig,
        rejected=rejected.tolist(),
        adjusted_pvalues=adj.tolist(),
        cutoff_pvalue=cutoff,
        implied_t_hurdle=implied_t,
    )

def bonferroni(pvalues: np.ndarray,alpha: float=0.05)->CorrectionResult:
    p=np.asarray(pvalues,dtype=float)
    m=p.size
    adj=np.minimum(p*m,1.0)
    rejected=p<=alpha/m
    return _finalize("Bonferroni",alpha,p,rejected,adj)


def holm(pvalues: np.ndarray,alpha: float=0.05)->CorrectionResult:
    p=np.asarray(pvalues,dtype=float)
    m=p.size
    order=np.argsort(p)
    sorted_p=p[order]
    adj_sorted=np.maximum.accumulate((m-np.arange(m))*sorted_p)
    adj_sorted=np.minimum(adj_sorted,1.0)
    adj=np.empty_like(adj_sorted)
    adj[order]=adj_sorted
    rejected=adj<=alpha
    return _finalize("Holm",alpha,p,rejected,adj)

def benjamini_hochberg(pvalues: np.ndarray,alpha: float=0.05)->CorrectionResult:
    p=np.asarray(pvalues,dtype=float)
    m=p.size
    order=np.argsort(p)
    sorted_p=p[order]
    ranks=np.arange(1,m+1)

    q_sorted=sorted_p*m/ranks
    q_sorted=np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted=np.minimum(q_sorted,1.0)
    adj=np.empty_like(q_sorted)
    adj[order]=q_sorted

    passing=sorted_p<=(ranks/m)*alpha
    if passing.any():
        kmax=np.max(np.where(passing)[0])
        reject_sorted=np.zeros(m,dtype=bool)
        reject_sorted[: kmax+1]=True
    else:
        reject_sorted=np.zeros(m,dtype=bool)
    rejected=np.empty(m,dtype=bool)
    rejected[order]=reject_sorted
    return _finalize("Benjamini-Hochberg",alpha,p,rejected,adj)

@dataclass
class HaircutResult:
    method: str
    naive_t_hurdle: float
    adjusted_t_hurdle: float
    adjusted_tstats: list[float]
    haircut_fraction: list[float]
    median_haircut: float

    def as_dict(self)->dict:
        return asdict(self)

def haircut_sharpe(
    tstats: np.ndarray,correction: CorrectionResult,
    naive_t_hurdle: float=2.0,)->HaircutResult:
    t_raw=np.abs(np.asarray(tstats,dtype=float))
    q=np.asarray(correction.adjusted_pvalues,dtype=float)
    t_adj=t_from_two_sided_pvalue(q)
    with np.errstate(divide="ignore",invalid="ignore"):
        hc=np.where(t_raw>0,1.0-t_adj/t_raw,np.nan)
    hc=np.clip(hc,0.0,1.0)
    return HaircutResult(
        method=correction.method,
        naive_t_hurdle=naive_t_hurdle,
        adjusted_t_hurdle=correction.implied_t_hurdle,
        adjusted_tstats=t_adj.tolist(),
        haircut_fraction=hc.tolist(),
        median_haircut=float(np.nanmedian(hc)),
    )