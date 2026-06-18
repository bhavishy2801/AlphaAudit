import { Github,FileText,BookOpen } from "lucide-react";
import type { Results } from "../types";

export default function Footer({ data }: { data: Results }) {
  return (
    <footer className="border-t border-line/70 bg-panel/40">
      <div className="mx-auto max-w-7xl px-5 py-12">
        <div className="grid gap-8 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <h3 className="text-lg font-bold text-white">AlphaAudit</h3>
            <p className="mt-2 max-w-md text-sm leading-relaxed text-sub">
              A reproducibility audit of the published equity-anomaly literature.
              Every statistic- the deflated Sharpe ratio,the probability of
              backtest overfitting,and the multiple-testing haircut- is
              implemented from the primary papers,not a black box.
            </p>
            <div className="mt-4 flex gap-2">
              <a
                href="https://github.com/bhavishy2801/AlphaAudit"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-line bg-panel2/60 px-3 py-2 text-sm text-slate-200 transition-colors hover:border-accent/60 hover:text-white"
             >
                <Github className="h-4 w-4" />Repository
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-slate-200">Methods</h4>
            <ul className="mt-3 space-y-2 text-sm text-sub">
              <li className="flex items-center gap-2"><BookOpen className="h-3.5 w-3.5" />Deflated Sharpe Ratio- Bailey & López de Prado</li>
              <li className="flex items-center gap-2"><BookOpen className="h-3.5 w-3.5" />PBO/CSCV- Bailey,Borwein,LdP,Zhu</li>
              <li className="flex items-center gap-2"><BookOpen className="h-3.5 w-3.5" />Multiple testing- Harvey,Liu & Zhu</li>
              <li className="flex items-center gap-2"><BookOpen className="h-3.5 w-3.5" />Decay- McLean & Pontiff</li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-slate-200">This run</h4>
            <ul className="mt-3 space-y-2 text-sm text-sub">
              <li className="flex items-center gap-2"><FileText className="h-3.5 w-3.5" />Source: {data.meta.data_source}</li>
              <li>{data.meta.n_anomalies} anomalies · {data.meta.n_months} months</li>
              <li>{data.meta.sample_start} → {data.meta.sample_end}</li>
              <li>Seed {data.meta.seed} · generated {new Date(data.meta.generated_at).toLocaleDateString()}</li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-line/60 pt-6 text-xs text-sub">
          The restraint is the point: this project audits whether published edges
          survive- it does not try to build one that beats them. A null result is
          still a result.
        </div>
      </div>
    </footer>
  );
}
