from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
from anomaly_audit.core import metrics

@dataclass
class DecayResult:

    pub_year: int
    n_is: int
    n_oos: int
    is_sharpe: float
    oos_sharpe: float
    is_tstat: float
    oos_tstat: float
    is_mean_ann: float
    oos_mean_ann: float
    decay_ratio: float
    decayed: bool

    def as_dict(self)->dict:
        return asdict(self)

def split_is_oos(
    returns: pd.Series,pub_year: int)->tuple[np.ndarray,np.ndarray]:
    
    idx=returns.index
    if isinstance(idx,pd.PeriodIndex):
        years=idx.year
    else:
        years=pd.DatetimeIndex(idx).year
    is_mask=years<=pub_year
    oos_mask=~is_mask
    return returns.to_numpy()[is_mask],returns.to_numpy()[oos_mask]

def decay_ratio(is_sharpe: float,oos_sharpe: float)->float:
    if not np.isfinite(is_sharpe) or abs(is_sharpe)<1e-8:
        return float("nan")
    return float(oos_sharpe/is_sharpe)

def analyze_decay(
    returns: pd.Series,
    pub_year: int,
    periods_per_year: int=metrics.ANNUALIZATION_DEFAULT,
    decay_threshold: float=0.5,)->DecayResult:
    is_r,oos_r=split_is_oos(returns,pub_year)
    is_sr=metrics.sharpe_ratio(is_r,periods_per_year)
    oos_sr=metrics.sharpe_ratio(oos_r,periods_per_year)
    dr=decay_ratio(is_sr,oos_sr)
    decayed=bool(np.isfinite(dr) and dr<decay_threshold)
    return DecayResult(
        pub_year=int(pub_year),n_is=int(np.isfinite(is_r).sum()),
        n_oos=int(np.isfinite(oos_r).sum()),
        is_sharpe=is_sr,oos_sharpe=oos_sr,
        is_tstat=metrics.t_statistic(is_r),oos_tstat=metrics.t_statistic(oos_r),
        is_mean_ann=metrics.annualized_return(is_r,periods_per_year),
        oos_mean_ann=metrics.annualized_return(oos_r,periods_per_year),
        decay_ratio=dr,decayed=decayed,
    )