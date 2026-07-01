import { motion } from "framer-motion";
import { ArrowDown,Database,GitCommitHorizontal,Sparkles } from "lucide-react";
import type { Results } from "../types";
import { fmt,pct } from "../lib/format";

const container={
  hidden: {},
  show: { transition: { staggerChildren: 0.09,delayChildren: 0.1 } },
};
const item={
  hidden: { opacity: 0,y: 26 },
  show: { opacity: 1,y: 0,transition: { duration: 0.8,ease: [0.16,1,0.3,1] } },
};

export default function Hero({ data }: { data: Results }) {
  const survivors=data.funnel[data.funnel.length-1];
  const decayLost =
    data.summary.median_decay_ratio===null
      ? null
      : (1-(data.summary.median_decay_ratio as number))*100;

  return (
    <header id="top" className="relative overflow-hidden pt-28 md:pt-36">
      <div className="mx-auto max-w-7xl px-5 pb-10">
        <motion.div variants={container} initial="hidden" animate="show">
          <motion.div variants={item}>
            <div className="inline-flex items-center gap-2 rounded-full border border-line/80 bg-panel2/50 px-3 py-1.5 text-xs font-medium text-accent2">
              <Sparkles className="h-3.5 w-3.5" />
              Reproducibility audit · deflated Sharpe · CSCV overfitting
            </div>
          </motion.div>

          <motion.h1
            variants={item}
            className="mt-6 max-w-4xl text-4xl font-black leading-[1.05] tracking-tight text-white sm:text-5xl md:text-6xl"
         >
            Do published equity anomalies{" "}
            <span className="grad-text">survive out-of-sample</span> and across{" "}
            <span className="grad-text">market regimes?</span>
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-6 max-w-2xl text-base leading-relaxed text-sub md:text-lg"
         >
            A systematic replication of{" "}
            <strong className="text-slate-200">{data.meta.n_anomalies}</strong>{" "}
            published anomalies, auditing how many keep their edge after the
            publication date and once you correct for the statistics of testing
            hundreds of signals at once.
          </motion.p>

          {/* headline figures */}
          <motion.div
            variants={item}
            className="mt-10 grid grid-cols-2 gap-3 sm:max-w-2xl sm:grid-cols-4"
         >
            <Headline value={`${survivors.count}`} label="survive every hurdle" accent="#10B981" />
            <Headline value={pct(survivors.pct,0)} label="of the universe" accent="#22D3EE" />
            <Headline value={decayLost===null ? "—" : pct(decayLost,0)} label="median Sharpe lost" accent="#F59E0B" />
            <Headline value={fmt(data.summary.pbo,2)} label="overfitting prob. (PBO)" accent="#A78BFA" />
          </motion.div>

          {/* meta badges */}
          <motion.div variants={item} className="mt-9 flex flex-wrap items-center gap-2.5 text-xs">
            <Badge icon={<Database className="h-3.5 w-3.5" />}>
              source: <span className="font-semibold text-slate-200">{data.meta.data_source}</span>
            </Badge>
            <Badge icon={<GitCommitHorizontal className="h-3.5 w-3.5" />}>
              {data.meta.sample_start} → {data.meta.sample_end} · {data.meta.n_months} months
            </Badge>
            <Badge>seed {data.meta.seed}</Badge>
            <Badge>{data.meta.n_trials} trials deflated</Badge>
          </motion.div>

          <motion.a
            variants={item}
            href="#funnel"
            className="mt-12 inline-flex items-center gap-2 text-sm font-medium text-sub transition-colors hover:text-white"
         >
            <span className="grid h-9 w-9 place-items-center rounded-full border border-line bg-panel2/60">
              <ArrowDown className="h-4 w-4 animate-bounce" />
            </span>
            Explore the audit
          </motion.a>
        </motion.div>
      </div>
    </header>
  );
}

function Headline({ value,label,accent }: { value: string; label: string; accent: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-panel/50 p-4 backdrop-blur-md">
      <div className="tnum text-3xl font-black tracking-tight" style={{ color: accent }}>
        {value}
      </div>
      <div className="mt-1 text-[11px] leading-tight text-sub">{label}</div>
    </div>
  );
}

function Badge({ children,icon }: { children: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line/70 bg-panel2/40 px-3 py-1.5 text-sub">
      {icon}
      {children}
    </span>
  );
}
