from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from anomaly_audit.config import Config
from anomaly_audit.pipeline.run import AuditResults

# house style
INK="#0B1221"
SUBINK="#5B6472"
GRID="#E6E9F0"
ACCENT="#6366F1"
ACCENT2="#22D3EE"
GOOD="#10B981"
WARN="#F59E0B"
BAD="#EF4444"
VERDICT_COLORS={
    "Robust": GOOD,"Regime-dependent": ACCENT,"Decayed": WARN,"Dead": BAD,
}
DIVERGING=LinearSegmentedColormap.from_list(
    "audit_div",["#B91C1C","#Fca5a5","#F4F4F5","#86EFAC","#15803D"]
)

def _style(ax):
    ax.set_facecolor("white")
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left","bottom"]:
        ax.spines[spine].set_color(GRID)
    ax.tick_params(colors=SUBINK,labelsize=9)
    ax.grid(axis="y",color=GRID,linewidth=0.8,zorder=0)
    ax.title.set_color(INK)
    return ax

def _save(fig,path: Path):
    fig.savefig(path,dpi=150,bbox_inches="tight",facecolor="white")
    plt.close(fig)

def fig_funnel(results: AuditResults,path: Path):
    funnel=results.funnel
    labels=[f["stage"] for f in funnel]
    counts=[f["count"] for f in funnel]
    n=counts[0]
    fig,ax=plt.subplots(figsize=(9,4.6))
    _style(ax)
    ax.grid(False)
    y=np.arange(len(labels))[::-1]
    cmap=LinearSegmentedColormap.from_list("fn",[ACCENT2,ACCENT])
    for i,(yy,c) in enumerate(zip(y,counts)):
        frac=c/n
        ax.barh(yy,frac,height=0.62,color=cmap(i/(len(labels)-1)),
                zorder=3,edgecolor="white",linewidth=1.5)
        ax.text(frac+0.012,yy,f"{c}  ({100*frac:.0f}%)",va="center",
                ha="left",fontsize=10,color=INK,fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels,fontsize=10,color=INK)
    ax.set_xlim(0,1.18)
    ax.set_xticks([])
    for spine in ["left","bottom"]:
        ax.spines[spine].set_visible(False)
    ax.set_title("Anomaly survival funnel",fontsize=14,fontweight="bold",loc="left",pad=12)
    _save(fig,path)

def fig_decay_distribution(results: AuditResults,path: Path):
    decays=np.array([d for d in results.decay_distribution if np.isfinite(d)])
    decays=np.clip(decays,-1.5,2.5)
    med=float(np.median(decays))
    fig,ax=plt.subplots(figsize=(8.5,4.4))
    _style(ax)
    ax.hist(decays,bins=28,color=ACCENT,alpha=0.85,zorder=3,edgecolor="white")
    ax.axvline(1.0,color=SUBINK,ls="--",lw=1.2,zorder=4,label="No decay (ratio=1)")
    ax.axvline(med,color=BAD,lw=2.0,zorder=5,label=f"Median={med:.2f}")
    ax.axvspan(-1.5,0,color=BAD,alpha=0.06,zorder=1)
    ax.set_xlabel("Decay ratio=OOS Sharpe/IS Sharpe",color=INK,fontsize=10)
    ax.set_ylabel("Anomalies",color=INK,fontsize=10)
    ax.set_title("Post-publication decay distribution",fontsize=14,fontweight="bold",loc="left",pad=12)
    ax.legend(frameon=False,fontsize=9,loc="upper right")
    _save(fig,path)

def fig_regime_heatmap(results: AuditResults,path: Path):
    regimes=results.regime_order
    df=pd.DataFrame(results.anomalies)
    rows=[]
    cats=sorted(df["category"].unique())
    for cat in cats:
        g=df[df["category"]==cat]
        row=[]
        for reg in regimes:
            vals=[a["regime_sharpes"].get(reg) for _,a in g.iterrows()]
            vals=[v for v in vals if v is not None and np.isfinite(v)]
            row.append(np.median(vals) if vals else np.nan)
        rows.append(row)
    mat=np.array(rows)

    fig,ax=plt.subplots(figsize=(9.5,5.2))
    vmax=np.nanmax(np.abs(mat))
    im=ax.imshow(mat,cmap=DIVERGING,vmin=-vmax,vmax=vmax,aspect="auto")
    ax.set_xticks(range(len(regimes)))
    ax.set_xticklabels(regimes,rotation=35,ha="right",fontsize=9,color=INK)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cats,fontsize=9,color=INK)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if np.isfinite(mat[i,j]):
                ax.text(j,i,f"{mat[i,j]:.2f}",ha="center",va="center",
                        fontsize=8,color=INK if abs(mat[i,j])<vmax*0.6 else "white")
    ax.set_title("Median annualized Sharpe by category x regime",
                 fontsize=14,fontweight="bold",loc="left",pad=12,color=INK)
    cbar=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.02)
    cbar.ax.tick_params(labelsize=8,colors=SUBINK)
    cbar.set_label("Annualized Sharpe",fontsize=9,color=SUBINK)
    _save(fig,path)

def fig_pbo(results: AuditResults,path: Path):
    pbo=results.pbo
    hist=pbo["logit_hist"]
    counts=np.array(hist["counts"])
    edges=np.array(hist["edges"])
    centers=(edges[:-1]+edges[1:])/2
    widths=np.diff(edges)
    fig,ax=plt.subplots(figsize=(8.5,4.4))
    _style(ax)
    colors=[BAD if c<0 else GOOD for c in centers]
    ax.bar(centers,counts,width=widths*0.95,color=colors,alpha=0.85,zorder=3,edgecolor="white")
    ax.axvline(0,color=INK,lw=1.4,zorder=4)
    ax.set_xlabel("Logit  ln(w/(1-w))   - negative=IS-best underperforms OOS",color=INK,fontsize=10)
    ax.set_ylabel("Combinatorial splits",color=INK,fontsize=10)
    ax.set_title(f"CSCV overfitting distribution   ·   PBO={pbo['pbo']:.2f}"
                 f"  (placebo {pbo['pbo_placebo']:.2f})",
                 fontsize=13,fontweight="bold",loc="left",pad=12)
    _save(fig,path)


def fig_dsr_scatter(results: AuditResults,path: Path):
    df=pd.DataFrame(results.anomalies)
    fig,ax=plt.subplots(figsize=(8.5,5.2))
    _style(ax)
    for verdict,color in VERDICT_COLORS.items():
        g=df[df["verdict"]==verdict]
        ax.scatter(g["is_sharpe"],g["oos_sharpe"],s=42,color=color,alpha=0.8,
                   edgecolor="white",linewidth=0.6,label=verdict,zorder=3)
    lim=[
        float(np.nanmin([df["is_sharpe"].min(),df["oos_sharpe"].min(),-0.2])),
        float(np.nanmax([df["is_sharpe"].max(),df["oos_sharpe"].max(),1.2])),
    ]
    ax.plot(lim,lim,color=SUBINK,ls="--",lw=1.0,zorder=2,label="No decay (OOS=IS)")
    ax.axhline(0,color=GRID,lw=1.0)
    ax.set_xlabel("In-sample annualized Sharpe",color=INK,fontsize=10)
    ax.set_ylabel("Out-of-sample annualized Sharpe",color=INK,fontsize=10)
    ax.set_title("In-sample vs out-of-sample Sharpe",fontsize=14,fontweight="bold",loc="left",pad=12)
    ax.legend(frameon=False,fontsize=8.5,loc="upper left",ncol=2)
    _save(fig,path)


def generate_all_figures(results: AuditResults,cfg: Config)->list[Path]:
    cfg.ensure_dirs()
    d=cfg.figures_dir
    plt.rcParams["font.family"]="DejaVu Sans"
    jobs=[
        ("funnel.png",fig_funnel),
        ("decay_distribution.png",fig_decay_distribution),
        ("regime_heatmap.png",fig_regime_heatmap),
        ("pbo_distribution.png",fig_pbo),
        ("is_oos_scatter.png",fig_dsr_scatter),
    ]
    paths=[]
    for fname,fn in jobs:
        p=d/fname
        fn(results,p)
        paths.append(p)
    return paths
