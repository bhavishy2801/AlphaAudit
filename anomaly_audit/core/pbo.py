r"""
Probability of Backtest Overfitting (PBO) via Combinatorially Symmetric
Cross-Validation (CSCV).

Primary source
--------------
Bailey,D.,Borwein,J.,Lopez de Prado,M. & Zhu,Q. (2017). *The Probability
of Backtest Overfitting.* Journal of Computational Finance.

What it measures
----------------
Given a matrix of ``N`` strategies' returns over ``T`` periods,CSCV asks: when
we pick the strategy that looks best **in-sample**,how often does it land in the
**bottom half** out-of-sample? That failure rate is the PBO - the probability
that an apparent edge is selection,not signal.

Method
------
1. Split the ``T`` rows into ``S`` equal,time-ordered blocks (``S`` even).
2. For every way of choosing ``S/2`` blocks as in-sample (``C(S,S/2)`` of them),
   the complement is out-of-sample.
3. Find the in-sample-best strategy ``n*``; compute its **relative rank**
   ``omega`` among all strategies out-of-sample,and the logit
   ``lambda=ln(omega/(1-omega))``.
4. ``PBO=P[lambda<=0]`` - the share of splits where the IS winner is an OOS
   below-median performer.
"""

from __future__ import annotations

from dataclasses import dataclass,asdict
from itertools import combinations

import numpy as np


@dataclass
class PBOResult:
    """Outcome of a CSCV run."""

    pbo: float                          # headline: P[OOS rank of IS-best<=median]
    n_combinations: int
    n_splits: int
    n_strategies: int
    logits: list[float]                 # lambda_c for each split
    relative_ranks: list[float]         # omega_c for each split
    is_perf_selected: list[float]       # IS Sharpe of the selected strategy
    oos_perf_selected: list[float]      # OOS Sharpe of the selected strategy
    prob_oos_loss: float                # P[selected strategy's OOS Sharpe<0]
    perf_degradation_slope: float       # OLS slope of OOS ~ IS perf (selected)

    def as_dict(self)->dict:
        d=asdict(self)
        # keep payload light: callers that want the raw arrays still have them,
        # but the JSON report stores a histogram instead.
        return d


def _block_sharpe_stats(returns: np.ndarray,n_splits: int):
    """Pre-compute per-block sum/sum-of-squares/count for fast Sharpe.

    Rows are trimmed to the largest multiple of ``n_splits`` so blocks are equal.
    Returns ``(block_sum,block_sqsum,block_len)`` with shapes
    ``(S,N),(S,N),int``.
    """
    M=np.asarray(returns,dtype=float)
    T,_=M.shape
    block_len=T // n_splits
    if block_len<2:
        raise ValueError(
            f"Not enough observations ({T}) for {n_splits} splits; "
            "need at least 2 rows per block."
        )
    usable=block_len*n_splits
    M=M[:usable]
    blocks=M.reshape(n_splits,block_len,M.shape[1])
    block_sum=blocks.sum(axis=1)               # (S,N)
    block_sqsum=(blocks**2).sum(axis=1)        # (S,N)
    return block_sum,block_sqsum,block_len


def _sharpe_from_moments(s: np.ndarray,q: np.ndarray,n: int)->np.ndarray:
    """Per-period Sharpe for each strategy from summed moments.

    ``s``=sum of returns,``q``=sum of squared returns,``n``=count.
    Uses the sample standard deviation (ddof=1).
    """
    mean=s/n
    var=(q-n*mean**2)/(n-1)
    var=np.where(var<=0,np.nan,var)
    return mean/np.sqrt(var)


def compute_pbo(returns: np.ndarray,n_splits: int=16)->PBOResult:
    """Run CSCV and return the full :class:`PBOResult`.

    Parameters
    ----------
    returns : array ``(T,N)`` of periodic returns; columns are strategies.
    n_splits : number of CSCV blocks ``S`` (even). ``C(S,S/2)`` combinations
        are evaluated.
    """
    if n_splits % 2 != 0:
        raise ValueError("n_splits (S) must be even for CSCV.")
    M=np.asarray(returns,dtype=float)
    N=M.shape[1]
    if N<2:
        raise ValueError("CSCV needs at least 2 strategies.")

    block_sum,block_sqsum,block_len=_block_sharpe_stats(M,n_splits)
    all_blocks=set(range(n_splits))
    half=n_splits // 2
    n_is=half*block_len

    logits: list[float]=[]
    ranks: list[float]=[]
    is_sel: list[float]=[]
    oos_sel: list[float]=[]
    oos_losses=0
    n_combos=0

    for combo in combinations(range(n_splits),half):
        is_idx=list(combo)
        oos_idx=list(all_blocks.difference(combo))

        s_is=block_sum[is_idx].sum(axis=0)
        q_is=block_sqsum[is_idx].sum(axis=0)
        s_oos=block_sum[oos_idx].sum(axis=0)
        q_oos=block_sqsum[oos_idx].sum(axis=0)

        sr_is=_sharpe_from_moments(s_is,q_is,n_is)
        sr_oos=_sharpe_from_moments(s_oos,q_oos,n_is)

        if np.all(np.isnan(sr_is)):
            continue
        n_star=int(np.nanargmax(sr_is))
        oos_star=sr_oos[n_star]
        if not np.isfinite(oos_star):
            continue

        # relative rank of the IS-best strategy,out-of-sample (1=worst,N=best)
        finite=np.isfinite(sr_oos)
        rank=int(np.sum(sr_oos[finite]<oos_star))+1
        omega=rank/(N+1)
        omega=min(max(omega,1e-6),1-1e-6)
        lam=float(np.log(omega/(1.0-omega)))

        logits.append(lam)
        ranks.append(float(omega))
        is_sel.append(float(sr_is[n_star]))
        oos_sel.append(float(oos_star))
        if oos_star<0:
            oos_losses+=1
        n_combos+=1

    if n_combos==0:
        raise RuntimeError("CSCV produced no valid combinations.")

    logits_arr=np.array(logits)
    pbo=float(np.mean(logits_arr<=0.0))
    prob_loss=oos_losses/n_combos

    # performance degradation: how IS edge maps to OOS edge for the selected pick
    x=np.array(is_sel)
    y=np.array(oos_sel)
    if x.size >= 2 and np.ptp(x)>0:
        slope=float(np.polyfit(x,y,1)[0])
    else:
        slope=float("nan")

    return PBOResult(
        pbo=pbo,
        n_combinations=n_combos,
        n_splits=n_splits,
        n_strategies=N,
        logits=logits,
        relative_ranks=ranks,
        is_perf_selected=is_sel,
        oos_perf_selected=oos_sel,
        prob_oos_loss=prob_loss,
        perf_degradation_slope=slope,
    )
