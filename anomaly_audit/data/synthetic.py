from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import skewnorm
from anomaly_audit.config import Config
from anomaly_audit.core import regimes as regime_core
from anomaly_audit.data.dataset import Dataset

ANOMALY_POOL: dict[str,list[str]]={
    "Value": [
        "BookToMarket","EarningsToPrice","CashFlowToPrice","SalesToPrice",
        "DividendYield","EnterpriseMultiple","NetPayoutYield","Leverage",
        "IntangibleValue","SalesGrowth","AssetGrowthValue","ResidualValue",
    ],
    "Momentum": [
        "Mom12m","Mom6m","Mom1m","IndustryMomentum","Mom52WeekHigh",
        "IntermediateMom","MomVolScaled","EarningsMomentum","ResidualMom",
        "MomSeasonality","PriceDelay","Mom36m",
    ],
    "Profitability": [
        "GrossProfitability","OperatingProfit","ROE","ROA","NetMargin",
        "CashProfitability","ProfitMargin","ReturnOnInvCap","GrossMargin",
        "EarningsConsistency","FCFYield","OperatingLeverage",
    ],
    "Investment": [
        "AssetGrowth","InvestmentToAssets","NetOperatingAssets","AccrualsTotal",
        "InvestmentGrowth","CapexGrowth","NetStockIssuance","CompositeIssuance",
        "ChNWC","DeltaPI","InventoryGrowth","AbnormalCapex",
    ],
    "Quality": [
        "PiotroskiFScore","OhlsonOScore","AltmanZ","QualityMinusJunk",
        "EarningsStability","DefaultProbability","CreditRating","DebtIssuance",
        "AssetTangibility","GovernanceIndex","AccrualQuality","EarningsSmooth",
    ],
    "Trading Frictions": [
        "Illiquidity","BidAskSpread","ShareVolume","DollarVolume","ZeroTrade",
        "MaxReturn","IdioVol","BetaArbitrage","ShortInterest","TurnoverVol",
        "AmihudILLIQ","RealizedVol",
    ],
    "Seasonality": [
        "JanuaryEffect","SameMonthReturn","TaxLossSelling","MonthOfYear",
        "Halloween","TurnOfMonth","EarningsSeasonality","DayOfWeek",
    ],
    "Behavioral": [
        "Disposition","AnalystDispersion","RevisionsUp","PEAD","FiftyTwoWk",
        "MediaSentiment","ShortReversal","LongReversal","Lottery",
        "OvernightReturn","NewsTone","AnalystCoverage",
    ],
}

REGIME_HOME_CHOICES=[
    "High Vol","Low Vol","Rising Rates","Falling Rates","Post-2018","Pre-2018",
]

CATEGORY_TURNOVER={
    "Value": 0.20,"Momentum": 1.10,"Profitability": 0.25,"Investment": 0.30,
    "Quality": 0.22,"Trading Frictions": 0.85,"Seasonality": 1.40,"Behavioral": 0.95,
}

def _build_name_universe(rng: np.random.Generator,n: int)->list[tuple[str,str]]:
    pairs: list[tuple[str,str]]=[]
    for cat,names in ANOMALY_POOL.items():
        for nm in names:
            pairs.append((nm,cat))
    rng.shuffle(pairs)
    if n<=len(pairs):
        return pairs[:n]
    extra=[]
    i=1
    while len(pairs)+len(extra)<n:
        nm,cat=pairs[(i-1) % len(pairs)]
        extra.append((f"{nm}_v{i//len(pairs)+2}",cat))
        i+=1
    return pairs+extra

def _macro_series(rng: np.random.Generator,index: pd.PeriodIndex)->pd.DataFrame:
    n=len(index)
    years=index.year.to_numpy()+(index.month.to_numpy()-1)/12.0
    log_vol=np.empty(n)
    log_vol[0]=np.log(16.0)
    phi,mu,sig=0.92,np.log(16.0),0.18
    shocks=rng.normal(0,sig,n)
    for t in range(1,n):
        log_vol[t]=mu+phi*(log_vol[t-1]-mu)+shocks[t]
    vol=np.exp(log_vol)
    crises={1974.0: 1.4,1987.8: 2.2,1998.7: 1.6,2001.7: 1.5,
              2008.8: 2.6,2011.7: 1.5,2020.2: 2.8,2022.5: 1.4}
    for yr,mult in crises.items():
        bump=mult*np.exp(-((years-yr) ** 2)/(0.10))
        vol=vol*(1.0+bump)
    vol=np.clip(vol,8.0,90.0)
    backbone=(
        6.0
       +8.0*np.exp(-((years-1981) ** 2)/(2*6.0**2))
       -3.0*(np.clip(years-1990,0,None)/35.0)
       +4.0*np.clip(years-2022,0,None)
    )
    rate=np.clip(backbone+rng.normal(0,0.25,n),0.05,18.0)
    term=1.5+1.2*np.sin((years-1970)/3.0)+rng.normal(0,0.3,n)
    return pd.DataFrame(
        {"volatility": vol,"rate": rate,"term_spread": term},index=index
    )

def _nonnormal_noise(
    rng: np.random.Generator,n: int,skew_a: float,jump_prob: float,jump_mult: float
)->np.ndarray:
    base=skewnorm.rvs(a=skew_a,size=n,random_state=rng)
    jumps=rng.normal(0,jump_mult,n)*(rng.random(n)<jump_prob)
    x=base+jumps
    x=x-x.mean()
    sd=x.std(ddof=0)
    return x/sd if sd>0 else x

def generate(cfg: Config)->Dataset:
    rng=np.random.default_rng(cfg.seed)
    d=cfg.data
    index=pd.period_range(d["sample_start"],d["sample_end"],freq="M")
    n_months=len(index)
    n_anom=int(d["n_anomalies"])
    macro=_macro_series(rng,index)
    regimes_df=regime_core.build_regimes(macro,cfg.regimes)
    membership=regime_core.regime_membership(regimes_df)
    pop=cfg.synthetic_population
    labels_order=["robust","decays","regime_dependent","false"]
    probs=np.array([pop[k] for k in labels_order],dtype=float)
    probs=probs/probs.sum()
    audit_labels=rng.choice(labels_order,size=n_anom,p=probs)
    names=_build_name_universe(rng,n_anom)
    gross=np.empty((n_months,n_anom))
    meta_rows=[]
    common=_nonnormal_noise(rng,n_months,skew_a=-2.0,jump_prob=0.04,jump_mult=2.5)
    sqrt12=np.sqrt(12.0)
    period_year=index.year.to_numpy()
    for j in range(n_anom):
        name,category=names[j]
        label=audit_labels[j]
        sigma_m=rng.uniform(0.018,0.045)
        skew_a=rng.uniform(-4.0,0.5)
        jump_prob=rng.uniform(0.02,0.06)
        beta=rng.uniform(0.0,0.30)
        pub_year=int(rng.integers(1995,2014))
        home_regime=""
        mean_path=np.zeros(n_months)
        is_mask=period_year<=pub_year
        oos_mask=~is_mask

        if label=="robust":
            alpha_is=rng.uniform(1.00,1.55)/sqrt12*sigma_m
            decay=rng.uniform(0.85,1.00)
            mean_path[is_mask]=alpha_is
            mean_path[oos_mask]=alpha_is*decay

        elif label=="decays":
            alpha_is=rng.uniform(0.60,1.10)/sqrt12*sigma_m
            decay=rng.uniform(0.15,0.45)
            mean_path[is_mask]=alpha_is
            mean_path[oos_mask]=alpha_is*decay

        elif label=="regime_dependent":
            home_regime=REGIME_HOME_CHOICES[int(rng.integers(0,len(REGIME_HOME_CHOICES)))]
            home_mask=membership[home_regime]
            alpha_home=rng.uniform(1.05,1.70)/sqrt12*sigma_m
            decay=rng.uniform(0.60,0.95)
            on=np.where(is_mask,alpha_home,alpha_home*decay)
            mean_path=np.where(home_mask,on,0.0)

        else:
            sr_fake_ann=rng.uniform(0.60,1.10)
            mean_path[is_mask]=sr_fake_ann/sqrt12*sigma_m
            mean_path[oos_mask]=rng.normal(0.0,0.02)*sigma_m # ~0,faint drift

        eps=_nonnormal_noise(rng,n_months,skew_a,jump_prob,jump_mult=rng.uniform(2.0,3.5))
        series=mean_path+sigma_m*(np.sqrt(1-beta**2)*eps+beta*common)
        gross[:,j]=series

        is_r=series[is_mask]
        is_sd=is_r.std(ddof=1)
        orig_t=float(is_r.mean()/(is_sd/np.sqrt(is_r.size))) if is_sd>0 else np.nan
        turnover=CATEGORY_TURNOVER.get(category,0.5)*rng.uniform(0.7,1.3)
        meta_rows.append(
            {
                "anomaly": name,"category": category,"pub_year": pub_year,
                "orig_tstat": round(orig_t,2),"turnover": round(turnover,3),
                "audit_label": label,"home_regime": home_regime,
                "monthly_vol": round(sigma_m,4),
            }
        )

    gross_panel=pd.DataFrame(gross,index=index,columns=[m["anomaly"] for m in meta_rows])
    meta=pd.DataFrame(meta_rows).set_index("anomaly")

    if cfg.costs.get("apply_costs",True):
        bps=cfg.costs["bps_per_turnover"]/1e4
        monthly_cost=(meta["turnover"].to_numpy()*bps)[None,:]
        net_panel=gross_panel-monthly_cost
    else:
        net_panel=gross_panel.copy()

    return Dataset(
        panel=net_panel,
        gross_panel=gross_panel,
        meta=meta,
        macro=macro,
        source="synthetic",
    )