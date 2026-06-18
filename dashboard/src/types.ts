// TypeScript mirror of the Python pipeline's results.json schema.
// Every numeric field can be null because the pipeline maps NaN/inf->null.

export type Num=number | null;

export interface Meta {
  generated_at: string;
  data_source: string;
  has_ground_truth: boolean;
  n_anomalies: number;
  n_trials: number;
  sample_start: string;
  sample_end: string;
  n_months: number;
  seed: number;
  sr_cross_sectional_variance: Num;
  dsr_threshold: number;
  naive_t_hurdle: number;
  fdr_alpha: number;
  dates: string[];
  regime_order: string[];
}

export interface Summary {
  median_decay_ratio: Num;
  mean_decay_ratio: Num;
  pct_decayed: Num;
  pbo: Num;
  n_robust: number;
  n_regime_dependent: number;
  n_decayed: number;
  n_dead: number;
  pct_survive_naive: Num;
  pct_survive_bh: Num;
  verdict_counts: Record<string,number>;
  ground_truth_counts?: Record<string,number>;
}

export interface FunnelStage {
  stage: string;
  count: number;
  pct: number;
  desc: string;
}

export type Verdict="Robust" | "Regime-dependent" | "Decayed" | "Dead";

export interface Anomaly {
  name: string;
  category: string;
  pub_year: number;
  orig_tstat: Num;
  turnover: Num;
  audit_label: string;
  home_regime: string;
  sharpe_full: Num;
  tstat_full: Num;
  skew: Num;
  kurtosis: Num;
  max_drawdown: Num;
  n_months: number;
  psr_full: Num;
  dsr_full: Num;
  min_trl: Num;
  expected_max_sr: Num;
  is_sharpe: Num;
  oos_sharpe: Num;
  is_tstat: Num;
  oos_tstat: Num;
  decay_ratio: Num;
  n_is: number;
  n_oos: number;
  dsr_is: Num;
  dsr_oos: Num;
  oos_pvalue: Num;
  regime_verdict: Verdict;
  n_regimes_significant: number;
  n_regimes_total: number;
  n_partitions_spanned: number;
  spanned_axes: string[];
  regime_sharpes: Record<string,Num>;
  regime_significant: Record<string,boolean>;
  equity_curve: number[];
  pub_index: number;
  bh_qvalue: Num;
  bh_significant: boolean;
  bonferroni_significant: boolean;
  haircut_fraction: Num;
  verdict: Verdict;
}

export interface PBO {
  pbo: Num;
  pbo_placebo: Num;
  n_combinations: number;
  n_splits: number;
  prob_oos_loss: Num;
  perf_degradation_slope: Num;
  logit_hist: { counts: number[]; edges: number[] };
  scatter: { is: number[]; oos: number[] };
}

export interface CorrectionBlock {
  n_significant: number;
  cutoff_pvalue?: Num;
  implied_t_hurdle: Num;
}

export interface MultipleTesting {
  fdr_alpha: number;
  naive_t_hurdle: number;
  n_naive_significant: number;
  bh: CorrectionBlock;
  bonferroni: CorrectionBlock;
  holm: CorrectionBlock;
  haircut: { median_haircut: Num; adjusted_t_hurdle: Num };
}

export interface CategorySummary {
  category: string;
  n: number;
  median_oos_sharpe: Num;
  median_decay: Num;
  n_robust: number;
  pct_survive_bh: Num;
}

export interface Results {
  meta: Meta;
  summary: Summary;
  funnel: FunnelStage[];
  anomalies: Anomaly[];
  pbo: PBO;
  multiple_testing: MultipleTesting;
  regime_order: string[];
  decay_distribution: number[];
  category_summary: CategorySummary[];
}
