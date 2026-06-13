from __future__ import annotations
import io
import ssl
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from anomaly_audit.config import Config
from anomaly_audit.data.dataset import Dataset

OSAP_HOMEPAGE="https://www.openassetpricing.com/"
KEN_FRENCH_FACTORS=(
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)
FRED_CSV="https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
FRED_VOL_SERIES="VIXCLS"
FRED_RATE_SERIES="DGS3MO"
FRED_TERM_SERIES="T10Y2Y"

def _ssl_ctx()->ssl.SSLContext:
    ctx=ssl.create_default_context()
    ctx.check_hostname=False
    ctx.verify_mode=ssl.CERT_NONE
    return ctx

def download_file(url: str,dest: Path,timeout: int=60)->Path:
    dest.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={"User-Agent": "anomaly-audit/1.0"})
    with urllib.request.urlopen(req,timeout=timeout,context=_ssl_ctx()) as r:
        data=r.read()
    dest.write_bytes(data)
    return dest

def fetch_fred_series(series_id: str,timeout: int=30)->pd.Series:
    url=FRED_CSV.format(series=series_id)
    req=urllib.request.Request(url,headers={"User-Agent": "anomaly-audit/1.0"})
    with urllib.request.urlopen(req,timeout=timeout,context=_ssl_ctx()) as r:
        text=r.read().decode("utf-8")
    df=pd.read_csv(io.StringIO(text))
    date_col,val_col=df.columns[0],df.columns[1]
    df[date_col]=pd.to_datetime(df[date_col],errors="coerce")
    df[val_col]=pd.to_numeric(df[val_col],errors="coerce")
    s=df.dropna().set_index(date_col)[val_col]
    s.name=series_id
    return s

def _macro_from_fred(index: pd.PeriodIndex)->pd.DataFrame | None:
    try:
        vol=fetch_fred_series(FRED_VOL_SERIES).resample("ME").mean()
        rate=fetch_fred_series(FRED_RATE_SERIES).resample("ME").mean()
        term=fetch_fred_series(FRED_TERM_SERIES).resample("ME").mean()
    except Exception:
        return None
    out=pd.DataFrame({"volatility": vol,"rate": rate,"term_spread": term})
    out.index=out.index.to_period("M")
    out=out.reindex(index).interpolate().bfill().ffill()
    if out["volatility"].isna().any() or out["rate"].isna().any():
        return None
    return out


def load_osap(cfg: Config)->Dataset:
    raw=cfg.data_raw_dir
    pred_path=raw/"PredictorLSretWide.csv"
    doc_path=raw/"SignalDoc.csv"
    if not pred_path.exists() or not doc_path.exists():
        raise FileNotFoundError(
            f"OSAP files not found in {raw}. Download PredictorLSretWide.csv and "
            f"SignalDoc.csv from {OSAP_HOMEPAGE} (see README) or use synthetic data."
        )
    pred=pd.read_csv(pred_path)
    date_col="date" if "date" in pred.columns else pred.columns[0]
    pred[date_col]=pd.to_datetime(pred[date_col],errors="coerce")
    pred=pred.dropna(subset=[date_col]).set_index(date_col)
    pred.index=pred.index.to_period("M")
    panel=pred.apply(pd.to_numeric,errors="coerce")/100.0
    start=pd.Period(cfg.data["sample_start"],freq="M")
    end=pd.Period(cfg.data["sample_end"],freq="M")
    panel=panel.loc[(panel.index>=start) & (panel.index<=end)]
    doc=pd.read_csv(doc_path)
    doc.columns=[c.strip() for c in doc.columns]
    acro_col="Acronym" if "Acronym" in doc.columns else doc.columns[0]
    doc=doc.set_index(acro_col)
    keep=[c for c in panel.columns if c in doc.index]
    panel=panel[keep]
    panel=panel.dropna(axis=1,how="all")
    keep=list(panel.columns)

    def _col(*candidates,default=np.nan):
        for c in candidates:
            if c in doc.columns:
                return doc.loc[keep,c]
        return pd.Series(default,index=keep)

    meta=pd.DataFrame(index=keep)
    meta.index.name="anomaly"
    meta["category"]=_col("Cat.Economic","Cat.Data",default="Uncategorized").astype(str)
    meta["pub_year"]=pd.to_numeric(_col("Year",default=2000),errors="coerce").fillna(2000).astype(int)
    meta["orig_tstat"]=pd.to_numeric(_col("T-Stat","TStat",default=np.nan),errors="coerce")
    meta["turnover"]=pd.to_numeric(_col("Turnover",default=0.5),errors="coerce").fillna(0.5)

    macro=_macro_from_fred(panel.index)
    if macro is None:
        from anomaly_audit.data.synthetic import _macro_series

        rng=np.random.default_rng(cfg.seed)
        macro=_macro_series(rng,panel.index)

    return Dataset(
        panel=panel,
        gross_panel=panel.copy(),
        meta=meta,
        macro=macro,
        source="osap",
    )