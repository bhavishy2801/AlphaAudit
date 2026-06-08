from __future__ import annotations
import numpy as np
ANNUALIZATION_DEFAULT=12

def _clean(returns: np.ndarray)->np.ndarray:
    r=np.asarray(returns,dtype=float).ravel()
    return r[np.isfinite(r)]

def sharpe_ratio(returns: np.ndarray,periods_per_year: int=ANNUALIZATION_DEFAULT)->float:
    r=_clean(returns)
    if r.size<2:
        return float("nan")
    sd=r.std(ddof=1)
    if sd==0:
        return float("nan")
    return float(r.mean()/sd*np.sqrt(periods_per_year))

def sharpe_ratio_periodic(returns: np.ndarray)->float:
    r=_clean(returns)
    if r.size<2:
        return float("nan")
    sd=r.std(ddof=1)
    if sd==0:
        return float("nan")
    return float(r.mean()/sd)

def t_statistic(returns: np.ndarray)->float:
    r=_clean(returns)
    n=r.size
    if n<2:
        return float("nan")
    sd=r.std(ddof=1)
    if sd==0:
        return float("nan")
    return float(r.mean()/(sd/np.sqrt(n)))

def annualized_return(returns: np.ndarray,periods_per_year: int=ANNUALIZATION_DEFAULT)->float:
    r=_clean(returns)
    if r.size==0:
        return float("nan")
    growth=np.prod(1.0+r)
    years=r.size/periods_per_year
    if years<=0 or growth<=0:
        return float("nan")
    return float(growth ** (1.0/years)-1.0)

def annualized_vol(returns: np.ndarray,periods_per_year: int=ANNUALIZATION_DEFAULT)->float:
    r=_clean(returns)
    if r.size<2:
        return float("nan")
    return float(r.std(ddof=1)*np.sqrt(periods_per_year))

def skewness(returns: np.ndarray)->float:
    r=_clean(returns)
    n=r.size
    if n<3:
        return 0.0
    m=r.mean()
    sd=r.std(ddof=0)
    if sd==0:
        return 0.0
    return float(np.mean(((r-m)/sd) ** 3))

def kurtosis(returns: np.ndarray)->float:
    r=_clean(returns)
    n=r.size
    if n<4:
        return 3.0
    m=r.mean()
    sd=r.std(ddof=0)
    if sd==0:
        return 3.0
    return float(np.mean(((r-m)/sd) ** 4))

def max_drawdown(returns: np.ndarray)->float:
    r=_clean(returns)
    if r.size==0:
        return float("nan")
    equity=np.cumprod(1.0+r)
    running_max=np.maximum.accumulate(equity)
    drawdown=equity/running_max-1.0
    return float(drawdown.min())

def cumulative_log_equity(returns: np.ndarray)->np.ndarray:
    r=np.asarray(returns,dtype=float).ravel()
    r=np.where(np.isfinite(r),r,0.0)
    return np.cumsum(np.log1p(np.clip(r,-0.99,None)))