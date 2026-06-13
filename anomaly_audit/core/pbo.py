from __future__ import annotations
from dataclasses import dataclass,asdict
from itertools import combinations
import numpy as np

@dataclass
class PBOResult:

    pbo: float
    n_combinations: int
    n_splits: int
    n_strategies: int
    logits: list[float]
    relative_ranks: list[float]
    is_perf_selected: list[float]
    oos_perf_selected: list[float]
    prob_oos_loss: float
    perf_degradation_slope: float

    def as_dict(self)->dict:
        d=asdict(self)
        return d


def _block_sharpe_stats(returns: np.ndarray,n_splits: int):
    M=np.asarray(returns,dtype=float)
    T,_=M.shape
    block_len=T//n_splits
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
    mean=s/n
    var=(q-n*mean**2)/(n-1)
    var=np.where(var<=0,np.nan,var)
    return mean/np.sqrt(var)


def compute_pbo(returns: np.ndarray,n_splits: int=16)->PBOResult:
    if n_splits%2!=0:
        raise ValueError("n_splits (S) must be even for CSCV.")
    M=np.asarray(returns,dtype=float)
    N=M.shape[1]
    if N<2:
        raise ValueError("CSCV needs at least 2 strategies.")

    block_sum,block_sqsum,block_len=_block_sharpe_stats(M,n_splits)
    all_blocks=set(range(n_splits))
    half=n_splits//2
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

    x=np.array(is_sel)
    y=np.array(oos_sel)
    if x.size>=2 and np.ptp(x)>0:
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