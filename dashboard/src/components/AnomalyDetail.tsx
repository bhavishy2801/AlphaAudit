import { motion,AnimatePresence } from "framer-motion";
import { X,TrendingUp,TrendingDown } from "lucide-react";
import type { Anomaly,Results } from "../types";
import { fmt,pct,signed,VERDICT_COLOR,VERDICT_BG,categoryColor,labelPretty } from "../lib/format";
import EquityCurve from "./EquityCurve";

export default function AnomalyDetail({
  anomaly,
  data,
  onClose,
}: {
  anomaly: Anomaly | null;
  data: Results;
  onClose: () =>void;
}) {
  return (
    <AnimatePresence>
      {anomaly && (
        <>
          <motion.div
            className="fixed inset-0 z-[60] bg-ink/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            className="fixed inset-y-0 right-0 z-[70] w-full max-w-2xl overflow-y-auto border-l border-line bg-panel/95 shadow-2xl backdrop-blur-2xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring",stiffness: 320,damping: 36 }}
         >
            <Body anomaly={anomaly} data={data} onClose={onClose} />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function Body({ anomaly,data,onClose }: { anomaly: Anomaly; data: Results; onClose: () =>void }) {
  const a=anomaly;
  const decayPositive=(a.decay_ratio ?? 0)>=0.5;

  return (
    <div className="p-6">
      {/* header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="chip"
              style={{ color: categoryColor(a.category),background: `${categoryColor(a.category)}1f` }}
           >
              {a.category}
            </span>
            <span className="text-xs text-sub">published {a.pub_year}</span>
          </div>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-white">{a.name}</h2>
          <div className="mt-2 flex items-center gap-2">
            <span
              className="chip font-semibold"
              style={{ color: VERDICT_COLOR[a.verdict],background: VERDICT_BG[a.verdict] }}
           >
              {a.verdict}
            </span>
            {data.meta.has_ground_truth && a.audit_label && (
              <span className="chip bg-white/5 text-sub">
                ground truth: {labelPretty[a.audit_label] ?? a.audit_label}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-panel2/60 text-sub transition-colors hover:text-white"
       >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* equity curve */}
      <div className="mt-6 rounded-xl border border-line/70 bg-panel2/40 p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Cumulative performance</h3>
          <div className="flex items-center gap-1 text-xs font-medium" style={{ color: decayPositive ? VERDICT_COLOR.Robust : VERDICT_COLOR.Decayed }}>
            {decayPositive ? <TrendingUp className="h-3.5 w-3.5" />: <TrendingDown className="h-3.5 w-3.5" />}
            decay ratio {fmt(a.decay_ratio,2)}
          </div>
        </div>
        <EquityCurve anomaly={a} dates={data.meta.dates} />
      </div>

      {/* IS vs OOS */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Panel title="In-sample" accent="#22D3EE">
          <Row label="Sharpe (ann.)" value={fmt(a.is_sharpe,2)} />
          <Row label="t-stat" value={fmt(a.is_tstat,2)} />
          <Row label="Deflated Sharpe" value={pct((a.dsr_is ?? 0)*100,0)} />
          <Row label="Months" value={`${a.n_is}`} />
        </Panel>
        <Panel title="Out-of-sample" accent="#F59E0B">
          <Row label="Sharpe (ann.)" value={fmt(a.oos_sharpe,2)} />
          <Row label="t-stat" value={fmt(a.oos_tstat,2)} />
          <Row label="Deflated Sharpe" value={pct((a.dsr_oos ?? 0)*100,0)} hi={(a.dsr_oos ?? 0)>=data.meta.dsr_threshold} />
          <Row label="Months" value={`${a.n_oos}`} />
        </Panel>
      </div>

      {/* diagnostics grid */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Mini label="Full Sharpe" value={fmt(a.sharpe_full,2)} />
        <Mini label="Max drawdown" value={pct((a.max_drawdown ?? 0)*100,0)} />
        <Mini label="Skew" value={signed(a.skew,2)} />
        <Mini label="Kurtosis" value={fmt(a.kurtosis,1)} />
        <Mini label="BH q-value" value={fmt(a.bh_qvalue,3)} />
        <Mini label="Orig. t-stat" value={fmt(a.orig_tstat,2)} />
        <Mini label="Turnover" value={fmt(a.turnover,2)} />
        <Mini label="Haircut" value={pct((a.haircut_fraction ?? 0)*100,0)} />
      </div>

      {/* regime breakdown */}
      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Regime breakdown</h3>
          <span className="text-xs text-sub">
            spans {a.n_partitions_spanned}/3 axes · sig. in {a.n_regimes_significant}/{a.n_regimes_total}
          </span>
        </div>
        <div className="space-y-2">
          {data.regime_order.map((reg) =>{
            const sr=a.regime_sharpes[reg];
            const sig=a.regime_significant[reg];
            const v=sr ?? 0;
            const wpos=Math.max(0,Math.min(1,v/1.6))*50;
            const wneg=Math.max(0,Math.min(1,-v/1.6))*50;
            return (
              <div key={reg} className="flex items-center gap-3">
                <span className="w-28 shrink-0 text-right text-[11px] text-sub">{reg}</span>
                <div className="relative h-4 flex-1 rounded bg-panel2/60">
                  <div className="absolute inset-y-0 left-1/2 w-px bg-line" />
                  <motion.div
                    className="absolute inset-y-0 rounded"
                    style={{
                      left: v>=0 ? "50%" : `${50-wneg}%`,
                      width: `${v>=0 ? wpos : wneg}%`,
                      background: v>=0 ? (sig ? "#10B981" : "#10b98188") : sig ? "#EF4444" : "#ef444488",
                    }}
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                  />
                </div>
                <span className="tnum w-12 shrink-0 text-right text-[11px] font-mono text-slate-300">
                  {fmt(sr,2)}
                </span>
                <span className="w-3 shrink-0">
                  {sig && <span className="block h-1.5 w-1.5 rounded-full bg-good" />}
                </span>
              </div>
            );
          })}
        </div>
        <p className="mt-2 text-[11px] text-sub">
          Green dot=significant (t ≥ 2) in that regime. Robust requires significance on
          both sides of each macro axis.
        </p>
      </div>
    </div>
  );
}

function Panel({ title,accent,children }: { title: string; accent: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line/70 bg-panel2/40 p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: accent }}>
        {title}
      </div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Row({ label,value,hi }: { label: string; value: string; hi?: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-sub">{label}</span>
      <span className={`tnum font-mono ${hi ? "font-bold text-good" : "text-slate-200"}`}>{value}</span>
    </div>
  );
}

function Mini({ label,value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line/60 bg-panel2/30 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-sub">{label}</div>
      <div className="tnum mt-0.5 font-mono text-sm font-semibold text-slate-200">{value}</div>
    </div>
  );
}
