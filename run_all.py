from __future__ import annotations
import argparse
import time
from anomaly_audit.config import load_config
from anomaly_audit.data import load_dataset
from anomaly_audit.pipeline import run_audit
from anomaly_audit.report import (
    write_markdown_report,
    write_results_json,
    write_summary_csv,
)
from anomaly_audit.viz import generate_all_figures

def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(description="Anomaly survival audit- full pipeline")
    p.add_argument("--config",default=None,help="path to config.yaml")
    p.add_argument("--source",default=None,choices=["auto","synthetic","osap"],
                   help="override data.source")
    p.add_argument("--seed",type=int,default=None,help="override the master seed")
    p.add_argument("--no-figures",action="store_true",help="skip static figures")
    return p.parse_args()

def main()->None:
    args=parse_args()
    t0=time.time()
    cfg=load_config(args.config)
    if args.source:
        cfg.raw["data"]["source"]=args.source
    if args.seed is not None:
        cfg.raw["seed"]=args.seed
    cfg.ensure_dirs()
    print("="*68)
    print("  ANOMALY SURVIVAL AUDIT")
    print("  Do published equity anomalies survive OOS and across regimes?")
    print("="*68)
    ds=load_dataset(cfg,verbose=True)
    print(f"[data] panel: {ds.n_months} months x {ds.n_anomalies} anomalies "
          f"({ds.source})")
    results=run_audit(ds,cfg,verbose=True)
    json_path=write_results_json(results,cfg)
    csv_path=write_summary_csv(results,cfg)
    report_path=write_markdown_report(results,cfg)
    print(f"[out ] {json_path.relative_to(cfg.root)}")
    print(f"[out ] {csv_path.relative_to(cfg.root)}")
    print(f"[out ] {report_path.relative_to(cfg.root)}")
    if not args.no_figures:
        figs=generate_all_figures(results,cfg)
        for f in figs:
            print(f"[fig ] {f.relative_to(cfg.root)}")
    funnel=results.funnel
    s=results.summary
    print("-"*68)
    print("  SURVIVAL FUNNEL")
    for f in funnel:
        bar="#"*int(round(f["pct"]/2.5))
        print(f"    {f['stage']:<30s} {f['count']:>4d}  {bar}")
    print("-"*68)
    surv=funnel[-1]
    print(f"  {surv['count']}/{results.meta['n_anomalies']} anomalies "
          f"({surv['pct']}%) survive every hurdle.")
    if s["median_decay_ratio"] is not None:
        print(f"  Median post-publication decay: "
              f"{(1-s['median_decay_ratio'])*100:.0f}% of Sharpe lost.")
    print(f"  PBO={results.pbo['pbo']:.2f}  (placebo {results.pbo['pbo_placebo']:.2f})")
    print(f"  Done in {time.time()-t0:.1f}s.")
    print("="*68)

if __name__=="__main__":
    main()