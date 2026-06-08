from __future__ import annotations
import json
import math
import shutil
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from anomaly_audit.config import Config
from anomaly_audit.pipeline.run import AuditResults

def _sanitize(obj: Any)->Any:
    if isinstance(obj,dict):
        return {str(_sanitize_key(k)): _sanitize(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj,(np.integer,)):
        return int(obj)
    if isinstance(obj,(np.floating,)):
        f=float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj,(np.bool_,)):
        return bool(obj)
    if isinstance(obj,float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj,(np.ndarray,)):
        return _sanitize(obj.tolist())
    return obj

def _sanitize_key(k: Any)->Any:
    if isinstance(k,(np.integer,)):
        return int(k)
    if isinstance(k,(np.floating,)):
        return float(k)
    return k

def write_results_json(results: AuditResults,cfg: Config)->Path:
    cfg.ensure_dirs()
    payload=_sanitize(results.to_dict())
    out=cfg.results_json
    out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    dash=cfg.dashboard_data
    dash.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(out,dash)
    return out

def write_summary_csv(results: AuditResults,cfg: Config)->Path:
    cfg.ensure_dirs()
    cols=[
        "name","category","pub_year","audit_label","verdict","is_sharpe","oos_sharpe",
        "decay_ratio","is_tstat","oos_tstat","dsr_is","dsr_oos","oos_pvalue","bh_qvalue",
        "bh_significant","regime_verdict","n_partitions_spanned","haircut_fraction",
        "skew","kurtosis","max_drawdown","n_months",
    ]
    df=pd.DataFrame(results.anomalies)
    cols=[c for c in cols if c in df.columns]
    df=df[cols].copy()
    df=df.sort_values("oos_sharpe",ascending=False,na_position="last")
    out=cfg.summary_csv
    df.to_csv(out,index=False,float_format="%.4f")
    return out

def write_markdown_report(results: AuditResults,cfg: Config)->Path:
    m=results.meta
    s=results.summary
    mt=results.multiple_testing
    pbo=results.pbo
    funnel=results.funnel
    def pct(x):
        return "n/a" if x is None else f"{x:.1f}%"
    def num(x,d=2):
        return "n/a" if x is None else f"{x:.{d}f}"
    lines: list[str]=[]
    lines.append("# Do Published Equity Anomalies Survive Out-of-Sample and Across Market Regimes?")
    lines.append("")
    lines.append("*A reproducibility audit with deflated Sharpe ratios and overfitting diagnostics.*")
    lines.append("")
    lines.append(f"> **Auto-generated from `results.json` on {m['generated_at']}.** "
                 f"Data source: **{m['data_source']}** · {m['n_anomalies']} anomalies · "
                 f"{m['sample_start']} to {m['sample_end']} ({m['n_months']} months) · seed {m['seed']}.")
    lines.append("")
    lines.append("## Headline finding")
    lines.append("")
    survivors=funnel[-1]["count"]
    lines.append(
        f"Of **{m['n_anomalies']} published anomalies**,**{survivors} "
        f"({pct(funnel[-1]['pct'])})** clear every hurdle: positive out-of-sample,"
        f"naive significance,Benjamini-Hochberg multiple-testing control,robustness "
        f"across macro regimes,and a deflated Sharpe ratio that survives the "
        f"selection adjustment for {m['n_trials']} trials. The median anomaly lost "
        f"**{pct(None if s['median_decay_ratio'] is None else (1-s['median_decay_ratio'])*100)}** "
        f"of its Sharpe after publication."
    )
    lines.append("")
    lines.append("## The survival funnel")
    lines.append("")
    lines.append("| Stage | Surviving | % of universe |")
    lines.append("|---|---:|---:|")
    for f in funnel:
        lines.append(f"| {f['stage']} | {f['count']} | {pct(f['pct'])} |")
    lines.append("")
    lines.append("![Survival funnel](figures/funnel.png)")
    lines.append("")
    lines.append("## Post-publication decay (McLean-Pontiff)")
    lines.append("")
    lines.append(
        f"- Median decay ratio (OOS Sharpe/IS Sharpe): **{num(s['median_decay_ratio'])}**\n"
        f"- Share of anomalies that lost >50% of their Sharpe: **{pct(s['pct_decayed'])}**"
    )
    lines.append("")
    lines.append("![Decay distribution](figures/decay_distribution.png)")
    lines.append("")
    lines.append("## Multiple testing")
    lines.append("")
    lines.append(
        f"- Anomalies clearing the naive `t>{mt['naive_t_hurdle']}` bar: "
        f"**{mt['n_naive_significant']}**\n"
        f"- Surviving Benjamini-Hochberg FDR control (alpha={mt['fdr_alpha']}): "
        f"**{mt['bh']['n_significant']}** "
        f"(effective t-hurdle ~ **{num(mt['bh']['implied_t_hurdle'])}**)\n"
        f"- Surviving Bonferroni: **{mt['bonferroni']['n_significant']}** "
        f"(effective t-hurdle ~ **{num(mt['bonferroni']['implied_t_hurdle'])}**)\n"
        f"- Median Harvey-Liu-Zhu Sharpe haircut: "
        f"**{pct(None if mt['haircut']['median_haircut'] is None else mt['haircut']['median_haircut']*100)}**"
    )
    lines.append("")
    lines.append("## Probability of Backtest Overfitting (CSCV)")
    lines.append("")
    lines.append(
        f"- PBO on the published panel: **{num(pbo['pbo'])}** over "
        f"{pbo['n_combinations']} combinatorial splits\n"
        f"- PBO on a pure-noise placebo (validation): **{num(pbo['pbo_placebo'])}** "
        f"(theory says ~0.50)\n"
        f"- Performance-degradation slope (OOS vs IS of the selected strategy): "
        f"**{num(pbo['perf_degradation_slope'])}**"
    )
    lines.append("")
    lines.append("![Regime survival heatmap](figures/regime_heatmap.png)")
    lines.append("")
    lines.append("## Verdict breakdown")
    lines.append("")
    lines.append("| Verdict | Count |")
    lines.append("|---|---:|")
    for k in ["Robust","Regime-dependent","Decayed","Dead"]:
        lines.append(f"| {k} | {s['verdict_counts'].get(k,0)} |")
    lines.append("")
    if m.get("has_ground_truth"):
        lines.append("> Because this run used the calibrated synthetic universe,the audit's "
                     "verdicts can be checked against the planted ground truth- see "
                     "`results.json->summary.ground_truth_counts` and the confusion "
                     "matrix in the notebook.")
        lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```bash\npython run_all.py        # regenerates results.json,this report and every figure\n```")
    lines.append("")

    out=cfg.root/"results"/"REPORT.md"
    out.write_text("\n".join(lines),encoding="utf-8")
    return out