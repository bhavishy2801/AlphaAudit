import type { Num,Verdict } from "../types";

export const fmt=(x: Num,d=2): string =>
  x===null || x===undefined || !isFinite(x as number)
    ? "—"
    : (x as number).toFixed(d);

export const pct=(x: Num,d=0): string =>
  x===null || x===undefined || !isFinite(x as number)
    ? "—"
    : `${(x as number).toFixed(d)}%`;

export const signed=(x: Num,d=2): string =>{
  if (x===null || !isFinite(x as number)) return "—";
  const v=x as number;
  return `${v>=0 ? "+" : ""}${v.toFixed(d)}`;
};

export const VERDICT_COLOR: Record<Verdict,string>= {
  Robust: "#10B981",
  "Regime-dependent": "#6366F1",
  Decayed: "#F59E0B",
  Dead: "#EF4444",
};

export const VERDICT_BG: Record<Verdict,string>= {
  Robust: "rgba(16,185,129,0.14)",
  "Regime-dependent": "rgba(99,102,241,0.14)",
  Decayed: "rgba(245,158,11,0.14)",
  Dead: "rgba(239,68,68,0.14)",
};

export const CATEGORY_COLOR: Record<string,string>= {
  Value: "#22D3EE",
  Momentum: "#F472B6",
  Profitability: "#34D399",
  Investment: "#A78BFA",
  Quality: "#60A5FA",
  "Trading Frictions": "#FBBF24",
  Seasonality: "#F87171",
  Behavioral: "#2DD4BF",
};

export const categoryColor=(c: string): string =>
  CATEGORY_COLOR[c] ?? "#94A3B8";

// diverging color for a Sharpe value in [-vmax,vmax]: red <- white->emerald
export function sharpeColor(v: Num,vmax=1.2): string {
  if (v===null || !isFinite(v as number)) return "#11182f";
  const t=Math.max(-1,Math.min(1,(v as number)/vmax));
  if (t>=0) {
    // white (255,255,255)->emerald (16,185,129)
    const r=Math.round(255-t*(255-16));
    const g=Math.round(255-t*(255-185));
    const b=Math.round(255-t*(255-129));
    return `rgb(${r},${g},${b})`;
  }
  // white->red (239,68,68)
  const a=-t;
  const r=Math.round(255-a*(255-239));
  const g=Math.round(255-a*(255-68));
  const b=Math.round(255-a*(255-68));
  return `rgb(${r},${g},${b})`;
}

export const labelPretty: Record<string,string>= {
  robust: "Robust (planted)",
  decays: "Decays (planted)",
  regime_dependent: "Regime-dependent (planted)",
  false: "False/data-snooped (planted)",
};
