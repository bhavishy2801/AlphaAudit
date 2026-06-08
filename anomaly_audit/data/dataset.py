from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass
class Dataset:

    panel: pd.DataFrame
    gross_panel: pd.DataFrame
    meta: pd.DataFrame
    macro: pd.DataFrame
    source: str

    @property
    def n_anomalies(self)->int:
        return self.panel.shape[1]
    @property
    def n_months(self)->int:
        return self.panel.shape[0]
    @property
    def has_ground_truth(self)->bool:
        return "audit_label" in self.meta.columns