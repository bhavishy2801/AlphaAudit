import { useMemo } from "react";
import { motion } from "framer-motion";
import { ShieldCheck,FlaskConical } from "lucide-react";
import type { Results } from "../types";
import { Section,SectionHeading,Card } from "./ui";
import { fmt } from "../lib/format";

export default function PBOSection({ data }: { data: Results }) {
  const pbo=data.pbo;
  const hist=pbo.logit_hist;
  const maxCount=Math.max(...hist.counts,1);
  const centers=useMemo(
    () =>hist.edges.slice(0,-1).map((e,i) =>(e + hist.edges[i + 1])/2),
    [hist]
  );

  return (
    <Section id="pbo">
      <SectionHeading
        eyebrow="Bailey · Borwein · López de Prado · Zhu"
        title="Probability of backtest overfitting"
        blurb="Combinatorially Symmetric Cross-Validation asks: when you pick the strategy that looks best in-sample, how often does it land in the bottom half out-of-sample? That failure rate is the PBO."
      />

      <div className="grid gap-4 lg:grid-cols-5">
        {/* gauge + placebo */}
        <Card className="lg:col-span-2" glow>
          <div className="flex items-center gap-2 text-slate-200">
            <ShieldCheck className="h-4 w-4 text-good" />
            <h3 className="text-sm font-semibold">PBO on the published panel</h3>
          </div>
          <div className="mt-4 flex items-center justify-center">
            <Gauge value={pbo.pbo ?? 0} />
          </div>

          <div className="mt-6 space-y-3">
            <Bar label="Published panel" value={pbo.pbo ?? 0} color="#10B981" icon={<ShieldCheck className="h-3.5 w-3.5" />} />
            <Bar label="Pure-noise placebo" value={pbo.pbo_placebo ?? 0} color="#8A93A6" icon={<FlaskConical className="h-3.5 w-3.5" />} />
          </div>
          <p className="mt-4 text-xs leading-relaxed text-sub">
            The placebo of pure-noise strategies returns PBO ≈{" "}
            <strong className="text-slate-200">{fmt(pbo.pbo_placebo,2)}</strong>- exactly
            the coin-flip a correct implementation must produce, validating the routine.
            The real panel sits far below, so its in-sample winner is{" "}
            <strong className="text-good">not</strong> a pure artifact of selection.
          </p>
        </Card>

        {/* logit distribution */}
        <Card className="lg:col-span-3">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">
              CSCV logit distribution
            </h3>
            <div className="text-xs text-sub">{pbo.n_combinations.toLocaleString()} splits</div>
          </div>
          <div className="relative flex h-60 items-end gap-[2px]">
            {hist.counts.map((c,i) =>{
              const neg=centers[i]<0;
              return (
                <div key={i} className="group relative flex h-full flex-1 items-end">
                  <motion.div
                    className="w-full rounded-t-[2px]"
                    style={{
                      background: neg
                        ? "linear-gradient(180deg,#ef4444,#7f1d1d)"
                        : "linear-gradient(180deg,#10b981,#065f46)",
                    }}
                    initial={{ height: 0 }}
                    whileInView={{ height: `${(c/maxCount)*100}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.7,delay: i*0.01 }}
                  />
                </div>
              );
            })}
            {/* zero line */}
            <ZeroLine centers={centers} />
          </div>
          <div className="mt-2 flex justify-between text-[11px]">
            <span className="text-bad">← IS-best underperforms OOS (overfit)</span>
            <span className="text-good">IS-best holds up OOS →</span>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3 border-t border-line/70 pt-4">
            <Mini label="PBO" value={fmt(pbo.pbo,3)} accent="#10B981" />
            <Mini label="P[OOS loss]" value={fmt(pbo.prob_oos_loss,3)} accent="#F59E0B" />
            <Mini label="Degradation slope" value={fmt(pbo.perf_degradation_slope,2)} accent="#A78BFA" />
          </div>
        </Card>
      </div>
    </Section>
  );
}

function Gauge({ value }: { value: number }) {
  const v=Math.max(0,Math.min(1,value));
  const r=64;
  const circ=Math.PI*r; // half circle
  return (
    <svg width="190" height="120" viewBox="0 0 190 120">
      <path d={arc(95,100,r,180,0)} fill="none" stroke="#1E263F" strokeWidth="14" strokeLinecap="round" />
      <motion.path
        d={arc(95,100,r,180,0)}
        fill="none"
        stroke="url(#pbograd)"
        strokeWidth="14"
        strokeLinecap="round"
        strokeDasharray={circ}
        initial={{ strokeDashoffset: circ }}
        whileInView={{ strokeDashoffset: circ-v*circ }}
        viewport={{ once: true }}
        transition={{ duration: 1.5,ease: [0.16,1,0.3,1] }}
      />
      <defs>
        <linearGradient id="pbograd" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#10B981" />
          <stop offset="0.6" stopColor="#F59E0B" />
          <stop offset="1" stopColor="#EF4444" />
        </linearGradient>
      </defs>
      <text x="95" y="92" textAnchor="middle" className="tnum" fontSize="34" fontWeight="900" fill="#fff">
        {v.toFixed(2)}
      </text>
      <text x="95" y="112" textAnchor="middle" fontSize="11" fill="#8A93A6">
        0=no overfit · 0.5=coin-flip
      </text>
    </svg>
  );
}

function arc(cx: number,cy: number,r: number,a0: number,a1: number) {
  const p=(a: number) =>{
    const rad=(a*Math.PI)/180;
    return [cx + r*Math.cos(rad),cy-r*Math.sin(rad)];
  };
  const [x0,y0]=p(a0);
  const [x1,y1]=p(a1);
  return `M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`;
}

function Bar({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: number;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-sub" style={{ color }}>
          {icon}
          {label}
        </span>
        <span className="tnum font-mono text-slate-300">{value.toFixed(3)}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-panel2/70">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          whileInView={{ width: `${value*100}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1.1,ease: [0.16,1,0.3,1] }}
        />
      </div>
    </div>
  );
}

function ZeroLine({ centers }: { centers: number[] }) {
  const min=centers[0];
  const max=centers[centers.length-1];
  const left=((0-min)/(max-min))*100;
  if (left<0 || left>100) return null;
  return (
    <div className="pointer-events-none absolute inset-y-0" style={{ left: `${left}%` }}>
      <div className="h-full w-px bg-white/40" />
    </div>
  );
}

function Mini({ label,value,accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="text-center">
      <div className="tnum text-lg font-bold" style={{ color: accent }}>
        {value}
      </div>
      <div className="text-[11px] text-sub">{label}</div>
    </div>
  );
}
