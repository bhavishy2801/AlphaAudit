import { useMemo,useState } from "react";
import { motion } from "framer-motion";
import { Search,ArrowUpDown,ChevronRight } from "lucide-react";
import clsx from "clsx";
import type { Anomaly,Results,Verdict } from "../types";
import { Section,SectionHeading } from "./ui";
import { fmt,VERDICT_COLOR,VERDICT_BG,categoryColor } from "../lib/format";
import AnomalyDetail from "./AnomalyDetail";

type SortKey="name" | "oos_sharpe" | "is_sharpe" | "decay_ratio" | "dsr_oos" | "oos_tstat";
const VERDICTS: (Verdict | "All")[]=["All","Robust","Regime-dependent","Decayed","Dead"];

export default function ExplorerSection({ data }: { data: Results }) {
  const [query,setQuery]=useState("");
  const [verdict,setVerdict]=useState<Verdict | "All">("All");
  const [category,setCategory]=useState<string>("All");
  const [sort,setSort]=useState<SortKey>("oos_sharpe");
  const [asc,setAsc]=useState(false);
  const [selected,setSelected]=useState<Anomaly | null>(null);

  const categories=useMemo(
    () =>["All",...Array.from(new Set(data.anomalies.map((a) =>a.category))).sort()],
    [data]
  );

  const rows=useMemo(() =>{
    let r=data.anomalies.filter((a) =>{
      if (verdict!=="All" && a.verdict!==verdict) return false;
      if (category!=="All" && a.category!==category) return false;
      if (query && !a.name.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
    r=[...r].sort((x,y) =>{
      const vx=(x[sort] ?? -Infinity) as number;
      const vy=(y[sort] ?? -Infinity) as number;
      if (sort==="name") return asc ? x.name.localeCompare(y.name) : y.name.localeCompare(x.name);
      return asc ? vx-vy : vy-vx;
    });
    return r;
  },[data,query,verdict,category,sort,asc]);

  const toggleSort=(k: SortKey) =>{
    if (sort===k) setAsc(!asc);
    else {
      setSort(k);
      setAsc(false);
    }
  };

  return (
    <Section id="explorer">
      <SectionHeading
        eyebrow="Drill down"
        title="Anomaly explorer"
        blurb="Every anomaly in the study,one click away. Filter,sort,then open any signal to see its in-sample/out-of-sample equity curve,deflated Sharpe,and full regime breakdown."
      />

      {/* controls */}
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative max-w-xs flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-sub" />
          <input
            value={query}
            onChange={(e) =>setQuery(e.target.value)}
            placeholder="Search anomalies…"
            className="w-full rounded-xl border border-line bg-panel2/50 py-2.5 pl-10 pr-3 text-sm text-slate-200 placeholder:text-sub focus:border-accent/60"
          />
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {VERDICTS.map((v) =>(
            <button
              key={v}
              onClick={() =>setVerdict(v)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                verdict===v ? "text-white" : "text-sub hover:text-slate-200"
              )}
              style={
                verdict===v
                  ? v==="All"
                    ? { background: "#232c49" }
                    : { background: VERDICT_BG[v as Verdict],color: VERDICT_COLOR[v as Verdict] }
                  : undefined
              }
           >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* category chips */}
      <div className="mb-4 flex flex-wrap gap-1.5">
        {categories.map((c) =>(
          <button
            key={c}
            onClick={() =>setCategory(c)}
            className={clsx(
              "rounded-full border px-3 py-1 text-xs transition-colors",
              category===c
                ? "border-accent/60 bg-accent/10 text-white"
                : "border-line bg-panel2/40 text-sub hover:text-slate-200"
            )}
         >
            {c}
          </button>
        ))}
      </div>

      {/* table */}
      <div className="card overflow-hidden p-0">
        <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1.2fr_auto] items-center gap-2 border-b border-line/70 px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-sub">
          <Th onClick={() =>toggleSort("name")} active={sort==="name"}>Anomaly</Th>
          <Th onClick={() =>toggleSort("is_sharpe")} active={sort==="is_sharpe"} right>IS SR</Th>
          <Th onClick={() =>toggleSort("oos_sharpe")} active={sort==="oos_sharpe"} right>OOS SR</Th>
          <Th onClick={() =>toggleSort("decay_ratio")} active={sort==="decay_ratio"} right>Decay</Th>
          <Th onClick={() =>toggleSort("dsr_oos")} active={sort==="dsr_oos"} right>DSR</Th>
          <div className="text-right">Verdict</div>
          <div className="w-5" />
        </div>

        <div className="max-h-[560px] overflow-y-auto">
          {rows.map((a,i) =>(
            <motion.button
              key={a.name}
              onClick={() =>setSelected(a)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: Math.min(i*0.01,0.3) }}
              className="grid w-full grid-cols-[2fr_1fr_1fr_1fr_1fr_1.2fr_auto] items-center gap-2 border-b border-line/40 px-4 py-3 text-left transition-colors hover:bg-panel2/50"
           >
              <div className="flex items-center gap-2.5 overflow-hidden">
                <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: categoryColor(a.category) }} />
                <div className="overflow-hidden">
                  <div className="truncate text-sm font-medium text-slate-100">{a.name}</div>
                  <div className="truncate text-[11px] text-sub">{a.category} · {a.pub_year}</div>
                </div>
              </div>
              <Cell value={fmt(a.is_sharpe,2)} />
              <Cell value={fmt(a.oos_sharpe,2)} strong color={(a.oos_sharpe ?? 0)>0 ? "#34D399" : "#F87171"} />
              <Cell value={fmt(a.decay_ratio,2)} />
              <Cell value={a.dsr_oos===null ? "—" : `${Math.round(a.dsr_oos*100)}%`} color={(a.dsr_oos ?? 0)>=data.meta.dsr_threshold ? "#34D399" : undefined} />
              <div className="flex justify-end">
                <span className="chip font-semibold" style={{ color: VERDICT_COLOR[a.verdict],background: VERDICT_BG[a.verdict] }}>
                  {a.verdict}
                </span>
              </div>
              <ChevronRight className="h-4 w-4 text-sub" />
            </motion.button>
          ))}
          {rows.length===0 && (
            <div className="px-4 py-10 text-center text-sm text-sub">No anomalies match those filters.</div>
          )}
        </div>
        <div className="border-t border-line/70 px-4 py-2.5 text-xs text-sub">
          Showing <span className="font-semibold text-slate-300">{rows.length}</span>of {data.anomalies.length} anomalies
        </div>
      </div>

      <AnomalyDetail anomaly={selected} data={data} onClose={() =>setSelected(null)} />
    </Section>
  );
}

function Th({
  children,
  onClick,
  active,
  right,
}: {
  children: React.ReactNode;
  onClick: () =>void;
  active: boolean;
  right?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "flex items-center gap-1 transition-colors hover:text-slate-200",
        right && "justify-end",
        active && "text-accent2"
      )}
   >
      {children}
      <ArrowUpDown className="h-3 w-3 opacity-60" />
    </button>
  );
}

function Cell({ value,strong,color }: { value: string; strong?: boolean; color?: string }) {
  return (
    <div
      className={clsx("tnum text-right font-mono text-sm",strong ? "font-semibold" : "text-slate-300")}
      style={color ? { color } : undefined}
   >
      {value}
    </div>
  );
}
