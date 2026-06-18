import { motion } from "framer-motion";
import { TrendingDown } from "lucide-react";
import type { Results } from "../types";
import { Section,SectionHeading,Reveal } from "./ui";

export default function FunnelSection({ data }: { data: Results }) {
  const funnel=data.funnel;
  const total=funnel[0].count;

  return (
    <Section id="funnel">
      <SectionHeading
        eyebrow="The headline result"
        title="The survival funnel"
        blurb="Each stage is a strictly harder hurdle than the last. An anomaly must clear all previous stages to reach the next- so the funnel can only narrow. Watch where the literature falls apart."
      />

      <div className="grid gap-3">
        {funnel.map((stage,i) =>{
          const frac=stage.count/total;
          const prev=i===0 ? stage.count : funnel[i-1].count;
          const dropped=prev-stage.count;
          return (
            <Reveal key={stage.stage} delay={i*0.08}>
              <div className="group card overflow-hidden p-0">
                <div className="relative">
                  {/* animated fill */}
                  <motion.div
                    className="absolute inset-y-0 left-0 grad-accent opacity-[0.16]"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${frac*100}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.1,delay: i*0.08,ease: [0.16,1,0.3,1] }}
                  />
                  <motion.div
                    className="absolute inset-y-0 left-0 w-1 grad-accent"
                    initial={{ scaleY: 0 }}
                    whileInView={{ scaleY: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6,delay: i*0.08 }}
                  />
                  <div className="relative flex items-center justify-between gap-4 px-5 py-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2.5">
                        <span className="tnum text-xs font-semibold text-sub">
                          {String(i + 1).padStart(2,"0")}
                        </span>
                        <h3 className="truncate text-base font-bold text-white">
                          {stage.stage}
                        </h3>
                      </div>
                      <p className="mt-1 text-xs text-sub">{stage.desc}</p>
                    </div>

                    <div className="flex shrink-0 items-center gap-5">
                      {dropped>0 && (
                        <div className="hidden items-center gap-1 text-xs font-medium text-bad/90 sm:flex">
                          <TrendingDown className="h-3.5 w-3.5" />−{dropped}
                        </div>
                      )}
                      <div className="text-right">
                        <div className="tnum text-2xl font-black text-white">
                          {stage.count}
                        </div>
                        <div className="tnum text-xs text-sub">{stage.pct}%</div>
                      </div>
                      {/* mini bar */}
                      <div className="hidden h-10 w-28 items-end gap-[3px] sm:flex">
                        <div className="relative h-full w-full overflow-hidden rounded-md bg-panel2/70">
                          <motion.div
                            className="absolute bottom-0 left-0 w-full grad-accent"
                            initial={{ height: 0 }}
                            whileInView={{ height: `${frac*100}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 1,delay: 0.2 + i*0.08 }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>

      <Reveal delay={0.2}>
        <p className="mt-6 text-sm text-sub">
          The deflated Sharpe ratio is deliberately the last and most binding
          hurdle: it asks whether an edge clears the bar you would expect the
          luckiest of <strong className="text-slate-200">{data.meta.n_trials}</strong>{" "}
          worthless strategies to post. Only{" "}
          <strong className="text-good">{funnel[funnel.length-1].count}</strong>{" "}
          anomalies clear everything.
        </p>
      </Reveal>
    </Section>
  );
}
