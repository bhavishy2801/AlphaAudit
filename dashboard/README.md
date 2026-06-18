# AlphaAudit- Dashboard

An interactive,animated single-page app that visualizes the audit's `results.json`.

Built with **React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion** (charts via Recharts and hand-rolled SVG). Fully static- no backend. It reads `public/results.json`,which the Python pipeline mirrors there on every run.

## Run it

```bash
# from the repo root,generate the data the dashboard reads:
python run_all.py

# then:
cd dashboard
npm install
npm run dev        # http://localhost:5173
```

If you see *"No results found"*,run `python run_all.py` from the project root first- that writes `dashboard/public/results.json`.

## Build for deployment

```bash
npm run build      #->dashboard/dist  (static; deploy anywhere)
npm run preview    # preview the production build
```

The build is base-relative (`base: "./"`),so the `dist/` folder works from any static host or subpath (GitHub Pages,Netlify,an S3 bucket,etc.). Commit a copy of `results.json` into `public/` before building so the deployed site has data.

## Sections

| Section | What it shows |
|---|---|
| **Hero** | The headline figures: survivors,decay,PBO |
| **Funnel** | Stage-by-stage attrition,animated |
| **Decay** | Decay-ratio histogram + IS-vs-OOS scatter |
| **Multiple testing** | Effective *t*-stat hurdles + Sharpe haircut |
| **Overfitting** | PBO gauge,CSCV logit distribution,noise placebo |
| **Regimes** | Category × regime Sharpe heatmap |
| **Explorer** | Searchable table → per-anomaly detail drawer (equity curve,DSR,regime breakdown) |

## Structure

```
src/
├── App.tsx                 # shell,loading/error states
├── types.ts                # TypeScript mirror of results.json
├── hooks/                  # data loader,count-up animation
├── lib/format.ts           # number formatting + color scales
└── components/             # one file per section + shared ui primitives
```
