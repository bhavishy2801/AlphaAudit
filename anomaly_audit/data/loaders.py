from __future__ import annotations
from anomaly_audit.config import Config
from anomaly_audit.data import synthetic
from anomaly_audit.data.dataset import Dataset
from anomaly_audit.data.download import load_osap

def load_dataset(cfg: Config,verbose: bool=True)->Dataset:
    source=str(cfg.data.get("source","auto")).lower()

    def _log(msg: str)->None:
        if verbose:
            print(msg)

    if source=="synthetic":
        _log("[data] source=synthetic | generating calibrated anomaly universe.")
        return synthetic.generate(cfg)

    if source=="osap":
        _log("[data] source=osap | loading real Open Source Asset Pricing panel.")
        return load_osap(cfg)
    
    try:
        ds=load_osap(cfg)
        _log("[data] source=auto | found OSAP files,using real data.")
        return ds
    except FileNotFoundError as exc:
        _log(f"[data] source=auto | no OSAP files ({exc.__class__.__name__}); "
             "falling back to synthetic.")
        return synthetic.generate(cfg)

__all__=["load_dataset","Dataset"]