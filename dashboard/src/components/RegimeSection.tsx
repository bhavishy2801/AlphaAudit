import { useMemo,useState } from "react";
import { motion } from "framer-motion";
import type { Results } from "../types";
import { Section,SectionHeading,Card,Reveal } from "./ui";
import { sharpeColor,fmt } from "../lib/format";

function median(xs: number[]): number | null {
  const v=xs.filter((x) =>Number.isFinite(x)).sort((a,b) =>a-b);
  if (!v.length) return null;
  const m=Math.floor(v.length/2);
  return v.length % 2 ? v[m] : (v[m-1] + v[m])/2;
}

export default function RegimeSection({ data }: { data: Results }) {
  const regimes=data.regime_order;
  const [hover,setHover]=useState<{ r: number; c: number } | null>(null);

  const categories=useMemo(
    () =>Array.from(new Set(data.anomalies.map((a) =>a.category))).sort(),
    [data]
  );

  const matrix=useMemo(() =>{
    return categories.map((cat) =>{
      const group=data.anomalies.filter((a) =>a.category===cat);
      return regimes.map((reg) =>{
        const vals=group
          .map((a) =>a.regime_sharpes[reg])
          .filter((x): x is number =>x!==null && Number.isFinite(x));
        return median(vals);
      });
    });
  },[categories,regimes,data]);

  const vmax=useMemo(() =>{
    let m=0.6;
    matrix.forEach((row) =>row.forEach((v) =>v!==null && (m=Math.max(m,Math.abs(v)))));
    return m;
  },[matrix]);

  return (
    <Section id="regimes">
      <SectionHeading
        eyebrow="The original contribution"
        title="Regime-conditional survival"
        blurb="Regimes are defined from exogenous macro variables fixed in advance- volatility terciles,the rate trend,a microstructure break- never optimized on returns. An anomaly is robust only if it works across the full span of each axis,not in one lucky corner."
      />

      <Card>
        <div className="overflow-x-auto pb-2">
          <div className="min-w-[680px]">
            {/* axis group headers */}
            <div
              className="grid items-end gap-1"
              style={{ gridTemplateColumns: `150px repeat(${regimes.length},minmax(0,1fr))` }}
           >
              <div />
              {regimes.map((reg) =>(
                <div key={reg} className="px-1 pb-2 text-center text-[11px] font-medium text-sub">
                  {reg}
                </div>
              ))}
            </div>

            {/* rows */}
            {categories.map((cat,r) =>(
              <Reveal key={cat} delay={r*0.04}>
                <div
                  className="grid items-center gap-1"
                  style={{ gridTemplateColumns: `150px repeat(${regimes.length},minmax(0,1fr))` }}
               >
                  <div className="truncate pr-3 text-right text-xs font-medium text-slate-300">
                    {cat}
                  </div>
                  {matrix[r].map((v,c) =>{
                    const active=hover && hover.r===r && hover.c===c;
                    return (
                      <motion.div
                        key={c}
                        className="relative aspect-[2/1] cursor-default rounded-md"
                        style={{ background: sharpeColor(v,vmax) }}
                        initial={{ opacity: 0,scale: 0.85 }}
                        whileInView={{ opacity: 1,scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.4,delay: 0.02*c }}
                        onMouseEnter={() =>setHover({ r,c })}
                        onMouseLeave={() =>setHover(null)}
                        animate={active ? { scale: 1.08,zIndex: 10 } : { scale: 1,zIndex: 1 }}
                     >
                        <span
                          className="tnum absolute inset-0 grid place-items-center text-[10px] font-semibold"
                          style={{ color: v!==null && Math.abs(v)>vmax*0.55 ? "#0B1020" : "#1E293B" }}
                       >
                          {v===null ? "" : v.toFixed(2)}
                        </span>
                        {active && (
                          <div className="pointer-events-none absolute -top-10 left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded-md border border-line bg-ink/95 px-2.5 py-1.5 text-[11px] shadow-card">
                            <div className="font-semibold text-white">{cat}</div>
                            <div className="text-sub">
                              {regimes[c]} · Sharpe {fmt(v,2)}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        {/* legend */}
        <div className="mt-5 flex items-center justify-between border-t border-line/70 pt-4">
          <span className="text-[11px] text-sub">Median annualized Sharpe within each regime</span>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-bad">−{vmax.toFixed(1)}</span>
            <div
              className="h-2.5 w-40 rounded-full"
              style={{
                background:
                  "linear-gradient(90deg,#ef4444,#fca5a5,#f4f4f5,#86efac,#15803d)",
              }}
            />
            <span className="text-[11px] text-good">+{vmax.toFixed(1)}</span>
          </div>
        </div>
      </Card>

      {/* verdict split */}
      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        {(
          [
            ["Robust",data.summary.verdict_counts["Robust"] ?? 0,"#10B981","work everywhere"],
            ["Regime-dependent",data.summary.verdict_counts["Regime-dependent"] ?? 0,"#6366F1","one corner only"],
            ["Decayed",data.summary.verdict_counts["Decayed"] ?? 0,"#F59E0B","edge faded post-pub"],
            ["Dead",data.summary.verdict_counts["Dead"] ?? 0,"#EF4444","no OOS edge"],
          ] as const
        ).map(([label,count,color,note],i) =>(
          <Reveal key={label} delay={i*0.06}>
            <Card>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                <span className="text-xs font-medium text-slate-300">{label}</span>
              </div>
              <div className="tnum mt-2 text-3xl font-black" style={{ color }}>
                {count}
              </div>
              <div className="text-[11px] text-sub">{note}</div>
            </Card>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
