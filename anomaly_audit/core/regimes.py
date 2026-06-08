r"""
Macro-regime construction and regime-conditional re-estimation.

This is the project's original contribution. The objection a reviewer will
raise is *"your regimes are curve-fit."* The defence,baked into the design
here,is that regimes are defined from **exogenous macro variables fixed in
advance** - volatility terciles,the sign of the rate trend,and a structural
break date - never optimized on anomaly returns.

For every anomaly we re-estimate its Sharpe and t-statistic *within* each regime
and classify it as:

- **Robust**          significant in at least ``robust_min_regimes`` regimes
- **Regime-dependent**  significant in at least one regime but fewer than that
- **Dead**            significant in no regime
"""

from __future__ import annotations

from dataclasses import dataclass,asdict

import numpy as np
import pandas as pd

from anomaly_audit.core import metrics


def build_regimes(macro: pd.DataFrame,cfg: dict)->pd.DataFrame:
    """Construct regime labels from macro variables.

    Parameters
    ----------
    macro : DataFrame indexed by month with at least columns ``volatility`` and
        ``rate`` (a short-rate level).
    cfg : the ``regimes`` block of the project config.

    Returns
    -------
    DataFrame with categorical columns ``vol_regime``,``rate_regime`` and
    ``break_regime`` aligned to ``macro.index``.
    """
    out=pd.DataFrame(index=macro.index)

    # Volatility terciles (exogenous: realized/implied vol,not returns).
    vol_labels=cfg["vol_tercile_labels"]
    out["vol_regime"]=pd.qcut(macro["volatility"],3,labels=vol_labels)

    # Rate trend: sign of the trailing 12-month change in the short rate.
    rate_change=macro["rate"].diff(12)
    rising,falling=cfg["rate_labels"][1],cfg["rate_labels"][0]
    out["rate_regime"]=np.where(rate_change >= 0,rising,falling)
    # first 12 months have no trailing change->mark by current vs first level
    seed_mask=rate_change.isna()
    out.loc[seed_mask,"rate_regime"]=np.where(
        macro["rate"][seed_mask] >= macro["rate"].iloc[0],rising,falling
    )

    # Structural break (pre/post microstructure shift).
    break_date=pd.Period(cfg["structural_break"],freq="M")
    pre,post=cfg["break_labels"]
    idx_periods=_as_period_index(out.index)
    out["break_regime"]=np.where(idx_periods<break_date,pre,post)

    return out


def _as_period_index(idx)->pd.PeriodIndex:
    if isinstance(idx,pd.PeriodIndex):
        return idx
    return pd.DatetimeIndex(idx).to_period("M")


def regime_membership(regimes: pd.DataFrame)->dict[str,np.ndarray]:
    """Flatten regime columns into ``{label: boolean mask}`` over the index.

    Produces one entry per distinct regime value across all dimensions,e.g.
    ``{"Low Vol": mask,"High Vol": mask,"Rising Rates": mask,"Pre-2018": ...}``.
    The masks are ordered dimension-by-dimension so figures read left-to-right.
    """
    membership: dict[str,np.ndarray]={}
    for col in regimes.columns:
        # preserve categorical order when present,else first-appearance order
        series=regimes[col]
        if isinstance(series.dtype,pd.CategoricalDtype):
            values=list(series.cat.categories)
        else:
            values=list(pd.unique(series.dropna()))
        for val in values:
            membership[str(val)]=(series==val).to_numpy()
    return membership


@dataclass
class RegimeStat:
    """Performance of one anomaly inside one regime."""

    regime: str
    n: int
    sharpe: float
    tstat: float
    significant: bool

    def as_dict(self)->dict:
        return asdict(self)


@dataclass
class RegimeVerdict:
    """Regime-conditional classification of a single anomaly.

    Robustness is defined on the *partition* level,not by a raw count of
    significant buckets. A macro axis (e.g. volatility) is "spanned" only if the
    anomaly is significant on **both** of its opposing sides (Low *and* High
    vol). An anomaly that earns its alpha only in high-volatility months is
    therefore correctly flagged regime-dependent,not robust - exactly the
    distinction the project exists to draw.
    """

    verdict: str                       # "Robust" | "Regime-dependent" | "Dead"
    n_regimes_significant: int
    n_regimes_total: int
    n_partitions_spanned: int
    spanned_axes: list[str]
    per_regime: dict[str,dict]        # regime->{sharpe,tstat,n,significant}

    def as_dict(self)->dict:
        return asdict(self)


def conditional_performance(
    returns: pd.Series,
    membership: dict[str,np.ndarray],
    partitions: list[tuple[str,str,str]],
    sig_t: float=2.0,
    robust_min_partitions: int=3,
    min_obs: int=12,
    periods_per_year: int=metrics.ANNUALIZATION_DEFAULT,
)->RegimeVerdict:
    """Re-estimate an anomaly within every regime and classify its robustness.

    Parameters
    ----------
    partitions : list of ``(axis_name,side_a_label,side_b_label)``
        The opposing pairs that define each macro axis,e.g.
        ``("Volatility","Low Vol","High Vol")``. An axis is spanned when the
        anomaly is significant on both sides.
    robust_min_partitions : how many axes must be spanned to be called Robust.
    """
    r=returns.to_numpy()
    per_regime: dict[str,dict]={}
    sig_map: dict[str,bool]={}
    n_sig=0

    for regime,mask in membership.items():
        sub=r[mask]
        sub=sub[np.isfinite(sub)]
        if sub.size<min_obs:
            stat=RegimeStat(regime,int(sub.size),float("nan"),float("nan"),False)
        else:
            sr=metrics.sharpe_ratio(sub,periods_per_year)
            t=metrics.t_statistic(sub)
            sig=bool(np.isfinite(t) and abs(t) >= sig_t and sr>0)
            stat=RegimeStat(regime,int(sub.size),sr,t,sig)
            if sig:
                n_sig+=1
        sig_map[regime]=stat.significant
        per_regime[regime]=stat.as_dict()

    spanned_axes=[
        axis for axis,a,b in partitions
        if sig_map.get(a,False) and sig_map.get(b,False)
    ]
    n_spanned=len(spanned_axes)

    if n_spanned >= robust_min_partitions:
        verdict="Robust"
    elif n_sig >= 1:
        verdict="Regime-dependent"
    else:
        verdict="Dead"

    return RegimeVerdict(
        verdict=verdict,
        n_regimes_significant=n_sig,
        n_regimes_total=len(membership),
        n_partitions_spanned=n_spanned,
        spanned_axes=spanned_axes,
        per_regime=per_regime,
    )
