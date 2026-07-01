import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { Results,Verdict } from "../types";
import { Section,SectionHeading,Card,Stat } from "./ui";
import { VERDICT_COLOR,fmt,pct } from "../lib/format";

const VERDICTS: Verdict[]=["Robust","Regime-dependent","Decayed","Dead"];

export default function DecaySection({ data }: { data: Results }) {
  const bins=useMemo(() =>histogram(data.decay_distribution,-1.5,2.5,26),[data]);
  const maxCount=Math.max(...bins.map((b) =>b.count),1);
  const median=data.summary.median_decay_ratio;

  const scatterByVerdict=useMemo(() =>{
    const g: Record<string,{ x: number; y: number; name: string }[]>= {};
    VERDICTS.forEach((v) =>(g[v]=[]));
    data.anomalies.forEach((a) =>{
      if (a.is_sharpe===null || a.oos_sharpe===null) return;
      g[a.verdict]?.push({ x: a.is_sharpe,y: a.oos_sharpe,name: a.name });
    });
    return g;
  },[data]);

  return (
    <Section id="decay">
      <SectionHeading
        eyebrow="McLean–Pontiff"
        title="Post-publication decay"
        blurb="Split each anomaly at its publication year: in-sample before, out-of-sample after. The decay ratio is OOS Sharpe ÷ IS Sharpe. Arbitrage tends to trade a public edge away- and it shows."
      />

      <div className="grid gap-4 lg:grid-cols-5">
        {/* histogram */}
        <Card className="lg:col-span-3">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              Distribution of decay ratios
            </h3>
            <div className="flex items-center gap-3 text-xs text-sub">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-accent" />count
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-px bg-bad" />median {fmt(median,2)}
              </span>
            </div>
          </div>

          <div className="relative h-56">
            <div className="flex h-full items-end gap-[2px]">
              {bins.map((b,i) =>{
                const isNeg=b.x1<=0;
                return (
                  <div key={i} className="group relative flex h-full flex-1 items-end">
                    <motion.div
                      className="w-full rounded-t-[3px]"
                      style={{
                        background: isNeg
                          ? "linear-gradient(180deg,#ef4444,#7f1d1d)"
                          : "linear-gradient(180deg,#22d3ee,#4f46e5)",
                      }}
                      initial={{ height: 0 }}
                      whileInView={{ height: `${(b.count/maxCount)*100}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8,delay: i*0.012,ease: [0.16,1,0.3,1] }}
                    />
                    <div className="pointer-events-none absolute -top-8 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-md border border-line bg-ink/95 px-2 py-1 text-[10px] text-slate-200 opacity-0 transition-opacity group-hover:opacity-100">
                      {b.count} · [{b.x0.toFixed(1)},{b.x1.toFixed(1)})
                    </div>
                  </div>
                );
              })}
            </div>
            {/* reference markers */}
            <Marker bins={bins} value={1} label="no decay" color="#8A93A6" />
            <Marker bins={bins} value={median ?? 0} label="median" color="#EF4444" />
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-sub">
            <span>reversed (&lt;0)</span>
            <span>fully decayed (0)</span>
            <span>no decay (1)</span>
            <span>stronger OOS (&gt;1)</span>
          </div>
        </Card>

        {/* stats + scatter */}
        <div className="grid gap-4 lg:col-span-2">
          <Card>
            <div className="grid grid-cols-2 gap-4">
              <Stat label="Median decay" value={fmt(median,2)} sub="OOS ÷ IS Sharpe" accent="#22D3EE" />
              <Stat
                label="Lost>50%"
                value={pct(data.summary.pct_decayed,0)}
                sub="of anomalies"
                accent="#F59E0B"
              />
            </div>
          </Card>
          <Card className="flex-1">
            <h3 className="mb-2 text-sm font-semibold text-slate-200">
              In-sample vs out-of-sample Sharpe
            </h3>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 8,right: 8,bottom: 18,left: -8 }}>
                  <CartesianGrid stroke="#1E263F" strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    name="IS Sharpe"
                    stroke="#8A93A6"
                    tick={{ fontSize: 10 }}
                    domain={[-0.5,"auto"]}
                    label={{ value: "IS Sharpe",position: "insideBottom",offset: -8,fill: "#8A93A6",fontSize: 11 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    name="OOS Sharpe"
                    stroke="#8A93A6"
                    tick={{ fontSize: 10 }}
                  />
                  <ZAxis range={[28,28]} />
                  <ReferenceLine
                    segment={[
                      { x: -0.5,y: -0.5 },
                      { x: 2,y: 2 },
                    ]}
                    stroke="#5B6472"
                    strokeDasharray="4 4"
                  />
                  <ReferenceLine y={0} stroke="#2A3350" />
                  <Tooltip
                    cursor={{ strokeDasharray: "3 3",stroke: "#6366F1" }}
                    contentStyle={tooltipStyle}
                    formatter={(v: number) =>fmt(v,2)}
                    labelFormatter={() =>""}
                  />
                  {VERDICTS.map((v) =>(
                    <Scatter
                      key={v}
                      name={v}
                      data={scatterByVerdict[v]}
                      fill={VERDICT_COLOR[v]}
                      fillOpacity={0.85}
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
              {VERDICTS.map((v) =>(
                <span key={v} className="flex items-center gap-1.5 text-[11px] text-sub">
                  <span className="h-2 w-2 rounded-full" style={{ background: VERDICT_COLOR[v] }} />
                  {v}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </Section>
  );
}

function Marker({
  bins,
  value,
  label,
  color,
}: {
  bins: Bin[];
  value: number;
  label: string;
  color: string;
}) {
  const min=bins[0].x0;
  const max=bins[bins.length-1].x1;
  const left=((value-min)/(max-min))*100;
  if (left<0 || left>100) return null;
  return (
    <div className="pointer-events-none absolute inset-y-0" style={{ left: `${left}%` }}>
      <div className="h-full w-px" style={{ background: color,opacity: 0.7 }} />
      <span
        className="absolute top-1 -translate-x-1/2 whitespace-nowrap text-[9px] font-medium"
        style={{ color }}
     >
        {label}
      </span>
    </div>
  );
}

interface Bin {
  x0: number;
  x1: number;
  x: number;
  count: number;
}

function histogram(values: number[],lo: number,hi: number,nbins: number): Bin[] {
  const bins: Bin[]=[];
  const w=(hi-lo)/nbins;
  for (let i=0; i<nbins; i++) {
    bins.push({ x0: lo + i*w,x1: lo + (i + 1)*w,x: lo + (i + 0.5)*w,count: 0 });
  }
  values.forEach((v) =>{
    const c=Math.max(lo,Math.min(hi-1e-9,v));
    const idx=Math.min(nbins-1,Math.floor((c-lo)/w));
    bins[idx].count += 1;
  });
  return bins;
}

const tooltipStyle={
  background: "#070B16",
  border: "1px solid #1E263F",
  borderRadius: 10,
  fontSize: 12,
  color: "#E2E8F0",
};
