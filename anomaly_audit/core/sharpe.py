r"""
Sharpe-ratio inference: standard error,Probabilistic Sharpe Ratio (PSR),and
the Deflated Sharpe Ratio (DSR).

Primary sources
---------------
- Bailey,D. & Lopez de Prado,M. (2012). *The Sharpe Ratio Efficient Frontier.*
  Journal of Risk.->PSR and the non-normal Sharpe standard error.
- Bailey,D. & Lopez de Prado,M. (2014). *The Deflated Sharpe Ratio: Correcting
  for Selection Bias,Backtest Overfitting and Non-Normality.* Journal of
  Portfolio Management.->expected maximum Sharpe and the DSR.

Why deflate?
------------
If you try ``N`` strategies,the *best* one's Sharpe is inflated purely by
selection. The DSR replaces the usual zero benchmark in the PSR with
``E[max SR]``-the Sharpe you would expect the luckiest of ``N`` truly worthless
strategies to post-and asks whether the observed Sharpe still clears it. It
also corrects for short samples and for non-normal (skewed/fat-tailed)
returns. The output is a probability that the *true* Sharpe is positive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass,asdict

import numpy as np
from scipy.stats import norm

from anomaly_audit.core import metrics

EULER_MASCHERONI=0.5772156649015329


# ---------------------------------------------------------------------------
#  Sharpe standard error & Probabilistic Sharpe Ratio
# ---------------------------------------------------------------------------
def sharpe_std_error(sr: float,n: int,skew: float,kurt: float)->float:
    r"""Standard error of the (per-period) Sharpe-ratio estimator.

    Mertens (2002)/Bailey & Lopez de Prado (2012):

    .. math::
        \hat\sigma(\widehat{SR}) =
            \sqrt{\frac{1-\gamma_3\,\widehat{SR}
                         +\frac{\gamma_4-1}{4}\,\widehat{SR}^2}{n-1}}

    where ``gamma_3`` is skewness and ``gamma_4`` is kurtosis (normal==3).
    """
    if n<2:
        return float("nan")
    radicand=1.0-skew*sr+(kurt-1.0)/4.0*sr**2
    radicand=max(radicand,1e-10)  # guard against extreme skew/kurt combos
    return math.sqrt(radicand/(n-1))


def probabilistic_sharpe_ratio(
    sr: float,n: int,skew: float,kurt: float,sr_benchmark: float=0.0
)->float:
    r"""Probability that the true Sharpe exceeds ``sr_benchmark``.

    .. math::
        \widehat{PSR}(SR^\ast) =
            \Phi\!\left(\frac{(\widehat{SR}-SR^\ast)\sqrt{n-1}}
                             {\sqrt{1-\gamma_3 \widehat{SR}
                                   +\frac{\gamma_4-1}{4}\widehat{SR}^2}}\right)

    All Sharpe inputs are *per-period* (non-annualized).
    """
    if not np.isfinite(sr) or n<2:
        return float("nan")
    se=sharpe_std_error(sr,n,skew,kurt)
    if not np.isfinite(se) or se==0:
        return float("nan")
    return float(norm.cdf((sr-sr_benchmark)/se))


def min_track_record_length(
    sr: float,skew: float,kurt: float,sr_benchmark: float=0.0,prob: float=0.95
)->float:
    r"""Minimum number of observations for the PSR to reach ``prob``.

    The minimum Track Record Length (minTRL) is how long a track record must be
    before we can assert,at confidence ``prob``,that its true Sharpe beats
    ``sr_benchmark``. Returns ``inf`` if the observed Sharpe does not exceed the
    benchmark at all.
    """
    if not np.isfinite(sr) or sr<=sr_benchmark:
        return float("inf")
    z=norm.ppf(prob)
    radicand=1.0-skew*sr+(kurt-1.0)/4.0*sr**2
    radicand=max(radicand,1e-10)
    return float(1.0+radicand*(z/(sr-sr_benchmark)) ** 2)


# ---------------------------------------------------------------------------
#  Deflated Sharpe Ratio
# ---------------------------------------------------------------------------
def expected_max_sharpe(sr_variance: float,n_trials: int)->float:
    r"""Expected maximum Sharpe across ``n_trials`` worthless strategies.

    Under the null that all trials have a true Sharpe of zero and their estimated
    Sharpes are i.i.d. ``N(0,sr_variance)``,the expected maximum is

    .. math::
        E[\max_n SR] \approx \sqrt{V}\,\Big[(1-\gamma)\,Z^{-1}\!\big(1-\tfrac1N\big)
                             +\gamma\,Z^{-1}\!\big(1-\tfrac1N e^{-1}\big)\Big]

    with ``gamma`` the Euler-Mascheroni constant and ``V`` the cross-sectional
    variance of the trials' (per-period) Sharpe ratios.
    """
    if n_trials<2 or not np.isfinite(sr_variance) or sr_variance<=0:
        return 0.0
    g=EULER_MASCHERONI
    sqrt_v=math.sqrt(sr_variance)
    maxz=norm.ppf(1.0-1.0/n_trials)
    maxz2=norm.ppf(1.0-1.0/(n_trials*math.e))
    return float(sqrt_v*((1.0-g)*maxz+g*maxz2))


def deflated_sharpe_ratio(
    sr: float,
    n: int,
    skew: float,
    kurt: float,
    n_trials: int,
    sr_variance: float,
)->float:
    """Deflated Sharpe Ratio: PSR benchmarked at the expected maximum Sharpe.

    Parameters
    ----------
    sr : per-period Sharpe ratio of the strategy under test.
    n : number of return observations.
    skew,kurt : skewness and (non-excess) kurtosis of the returns.
    n_trials : number of strategies that were searched over (the breadth).
    sr_variance : cross-sectional variance of the trials' per-period Sharpes.
    """
    sr_star=expected_max_sharpe(sr_variance,n_trials)
    return probabilistic_sharpe_ratio(sr,n,skew,kurt,sr_benchmark=sr_star)


# ---------------------------------------------------------------------------
#  High-level convenience: full Sharpe report for one return series
# ---------------------------------------------------------------------------
@dataclass
class SharpeReport:
    """All Sharpe-related statistics for a single excess-return series."""

    n: int
    sharpe_annual: float
    sharpe_periodic: float
    t_stat: float
    skew: float
    kurt: float
    psr: float                 # P[true SR>0],non-normality+short-sample adjusted
    dsr: float                 # P[true SR>E[max SR]],also corrects for N trials
    expected_max_sr_periodic: float
    min_track_record_length: float

    def as_dict(self)->dict:
        return asdict(self)


def sharpe_report(
    returns: np.ndarray,
    n_trials: int,
    sr_variance: float,
    periods_per_year: int=metrics.ANNUALIZATION_DEFAULT,
)->SharpeReport:
    """Compute the full Sharpe report (annualized SR,PSR,DSR,minTRL) at once.

    ``n_trials`` and ``sr_variance`` describe the *search* the strategy came from
    and drive the deflation; they are properties of the whole anomaly panel.
    """
    r=metrics._clean(returns)
    n=int(r.size)
    sr_p=metrics.sharpe_ratio_periodic(r)
    sk=metrics.skewness(r)
    ku=metrics.kurtosis(r)
    sr_star=expected_max_sharpe(sr_variance,n_trials)

    return SharpeReport(
        n=n,
        sharpe_annual=metrics.sharpe_ratio(r,periods_per_year),
        sharpe_periodic=sr_p,
        t_stat=metrics.t_statistic(r),
        skew=sk,
        kurt=ku,
        psr=probabilistic_sharpe_ratio(sr_p,n,sk,ku,sr_benchmark=0.0),
        dsr=probabilistic_sharpe_ratio(sr_p,n,sk,ku,sr_benchmark=sr_star),
        expected_max_sr_periodic=sr_star,
        min_track_record_length=min_track_record_length(sr_p,sk,ku,0.0,0.95),
    )


def cross_sectional_sr_variance(
    returns_matrix: np.ndarray,
)->float:
    """Variance of per-period Sharpe ratios across the columns of a return matrix.

    ``returns_matrix`` is ``(T observations,N strategies)``. This is the ``V``
    that feeds :func:`expected_max_sharpe`.
    """
    mat=np.asarray(returns_matrix,dtype=float)
    srs=[]
    for j in range(mat.shape[1]):
        col=mat[:,j]
        srs.append(metrics.sharpe_ratio_periodic(col))
    srs=np.array([s for s in srs if np.isfinite(s)])
    if srs.size<2:
        return float("nan")
    return float(srs.var(ddof=1))
