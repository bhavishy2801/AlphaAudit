from __future__ import annotations
import os
from dataclasses import dataclass,field
from pathlib import Path
from typing import Any
import yaml

def project_root()->Path:
    here=Path(__file__).resolve()
    for parent in [here,*here.parents]:
        if (parent/"config.yaml").exists():
            return parent
    return here.parents[1] #fallback to two levels up if config.yaml not found


@dataclass
class Config:

    raw: dict[str,Any]
    root: Path

    # convenience accessors
    @property
    def seed(self)->int:
        return int(self.raw["seed"])

    @property
    def data(self)->dict[str,Any]:
        return self.raw["data"]

    @property
    def synthetic_population(self)->dict[str,float]:
        return self.raw["synthetic_population"]

    @property
    def statistics(self)->dict[str,Any]:
        return self.raw["statistics"]

    @property
    def pbo(self)->dict[str,Any]:
        return self.raw["pbo"]

    @property
    def regimes(self)->dict[str,Any]:
        return self.raw["regimes"]

    @property
    def costs(self)->dict[str,Any]:
        return self.raw["costs"]

    # resolved paths
    def path(self,key: str)->Path:
        rel=self.raw["output"][key]
        p=(self.root/rel).resolve()
        return p

    @property
    def results_json(self)->Path:
        return self.path("results_json")

    @property
    def summary_csv(self)->Path:
        return self.path("summary_csv")

    @property
    def figures_dir(self)->Path:
        return self.path("figures_dir")

    @property
    def dashboard_data(self)->Path:
        return self.path("dashboard_data")

    @property
    def data_raw_dir(self)->Path:
        return (self.root/"data"/"raw").resolve()

    @property
    def data_processed_dir(self)->Path:
        return (self.root/"data"/"processed").resolve()

    def ensure_dirs(self)->None:
        for d in [
            self.results_json.parent,
            self.summary_csv.parent,
            self.figures_dir,
            self.dashboard_data.parent,
            self.data_raw_dir,
            self.data_processed_dir,
        ]:
            d.mkdir(parents=True,exist_ok=True)


def load_config(path: str | os.PathLike[str] | None=None)->Config:
    root=project_root()
    cfg_path=Path(path) if path is not None else root/"config.yaml"
    with open(cfg_path,"r",encoding="utf-8") as fh:
        raw=yaml.safe_load(fh)
    return Config(raw=raw,root=root)
