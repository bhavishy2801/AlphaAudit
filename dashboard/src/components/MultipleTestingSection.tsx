import { motion } from "framer-motion";
import { Scissors } from "lucide-react";
import type { Results } from "../types";
import { Section,SectionHeading,Card,Reveal } from "./ui";
import { fmt,pct } from "../lib/format";

export default function MultipleTestingSection({ data }: { data: Results }) {
  const mt=data.multiple_testing;
  const tMax=4.2;

  const methods=[
    { name: "Naive bar",t: mt.naive_t_hurdle,n: mt.n_naive_significant,color: "#EF4444",note: "t>2.0, ignores the search" },
    { name: "Benjamini–Hochberg",t: mt.bh.implied_t_hurdle,n: mt.bh.n_significant,color: "#F59E0B",note: `FDR control @ ${mt.fdr_alpha}` },
    { name: "Holm",t: mt.holm.implied_t_hurdle,n: mt.holm.n_significant,color: "#22D3EE",note: "step-down FWER" },
    { name: "Bonferroni",t: mt.bonferroni.implied_t_hurdle,n: mt.bonferroni.n_significant,color: "#A78BFA",note: "family-wise, strictest" },
  ];

  return (
    <Section id="testing">
      <SectionHeading
        eyebrow="Harvey–Liu–Zhu"
        title="The multiple-testing tax"
        blurb="The literature is one giant uncontrolled experiment. Test hundreds of signals and a t>2 bar guarantees false positives. Raising the bar to control the false-discovery rate quietly kills a chunk of the survivors."
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {/* hurdle escalation */}
        <Card className="lg:col-span-2">
          <h3 className="mb-5 text-sm font-semibold text-slate-200">
            How high should the t-stat bar really be?
          </h3>
          <div className="space-y-5">
            {methods.map((m,i) =>{
              const t=m.t ?? 0;
              const left=Math.min(100,(t/tMax)*100);
              return (
                <Reveal key={m.name} delay={i*0.07}>
                  <div>
                    <div className="mb-1.5 flex items-baseline justify-between text-sm">
                      <span className="font-medium text-slate-200">{m.name}</span>
                      <span className="text-xs text-sub">{m.note}</span>
                    </div>
                    <div className="relative h-9 rounded-lg bg-panel2/60">
                      {/* axis ticks */}
                      {[2,3,4].map((tick) =>(
                        <div
                          key={tick}
                          className="absolute inset-y-0 w-px bg-line"
                          style={{ left: `${(tick/tMax)*100}%` }}
                       >
                          <span className="absolute -bottom-5 -translate-x-1/2 text-[9px] text-sub">
                            {tick}
                          </span>
                        </div>
                      ))}
                      <motion.div
                        className="absolute inset-y-0 left-0 rounded-lg"
                        style={{ background: `linear-gradient(90deg,${m.color}22,${m.color}66)` }}
                        initial={{ width: 0 }}
                        whileInView={{ width: `${left}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 1,delay: i*0.07,ease: [0.16,1,0.3,1] }}
                      />
                      <motion.div
                        className="absolute inset-y-1 w-1 rounded-full"
                        style={{ background: m.color,boxShadow: `0 0 12px ${m.color}` }}
                        initial={{ left: 0,opacity: 0 }}
                        whileInView={{ left: `calc(${left}%-2px)`,opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 1,delay: i*0.07 }}
                      />
                      <div className="absolute inset-y-0 right-3 flex items-center gap-3 text-xs">
                        <span className="tnum font-mono text-slate-300">t ≈ {fmt(m.t,2)}</span>
                        <span className="tnum font-bold text-white">{m.n}</span>
                        <span className="text-sub">survive</span>
                      </div>
                    </div>
                  </div>
                </Reveal>
              );
            })}
          </div>
          <p className="mt-7 text-xs text-sub">
            Each row shows the effective t-stat hurdle the correction imposes and how
            many of the {data.meta.n_anomalies} anomalies clear it out-of-sample.
          </p>
        </Card>

        {/* haircut */}
        <Card glow>
          <div className="flex items-center gap-2 text-slate-200">
            <Scissors className="h-4 w-4 text-accent2" />
            <h3 className="text-sm font-semibold">Sharpe haircut</h3>
          </div>
          <div className="mt-5 flex flex-col items-center">
            <Donut value={(data.multiple_testing.haircut.median_haircut ?? 0)*100} />
            <p className="mt-4 text-center text-xs text-sub">
              Median fraction of the t-statistic (and therefore the Sharpe) that the
              Benjamini–Hochberg adjustment haircuts away across the whole signal set.
            </p>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 border-t border-line/70 pt-4 text-center">
            <div>
              <div className="tnum text-xl font-bold text-white">
                {pct(data.summary.pct_survive_naive,0)}
              </div>
              <div className="text-[11px] text-sub">survive naive bar</div>
            </div>
            <div>
              <div className="tnum text-xl font-bold text-accent2">
                {pct(data.summary.pct_survive_bh,0)}
              </div>
              <div className="text-[11px] text-sub">survive BH-FDR</div>
            </div>
          </div>
        </Card>
      </div>
    </Section>
  );
}

function Donut({ value }: { value: number }) {
  const r=52;
  const c=2*Math.PI*r;
  const v=Math.max(0,Math.min(100,value));
  return (
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx="70" cy="70" r={r} fill="none" stroke="#1E263F" strokeWidth="14" />
      <motion.circle
        cx="70"
        cy="70"
        r={r}
        fill="none"
        stroke="url(#hcgrad)"
        strokeWidth="14"
        strokeLinecap="round"
        transform="rotate(-90 70 70)"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        whileInView={{ strokeDashoffset: c-(v/100)*c }}
        viewport={{ once: true }}
        transition={{ duration: 1.4,ease: [0.16,1,0.3,1] }}
      />
      <defs>
        <linearGradient id="hcgrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22D3EE" />
          <stop offset="1" stopColor="#6366F1" />
        </linearGradient>
      </defs>
      <text x="70" y="66" textAnchor="middle" className="tnum" fontSize="26" fontWeight="800" fill="#fff">
        {v.toFixed(0)}%
      </text>
      <text x="70" y="86" textAnchor="middle" fontSize="10" fill="#8A93A6">
        median haircut
      </text>
    </svg>
  );
}
