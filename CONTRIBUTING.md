# Contributing to AlphaAudit

Thanks for your interest. This project is a reproducibility audit,so the bar for
contributions is the same bar the project holds itself to: every change must keep
the study one-command reproducible and every statistic traceable to a source.

## Ground rules

1. **Reproducibility first.** `python run_all.py` must regenerate `results.json`,
   the figures and the report deterministically from `config.yaml`. If your change
   touches the pipeline,re-run it and commit the refreshed outputs.
2. **No black boxes.** Core statistics (DSR,PBO,multiple testing) are implemented
   from primary papers. New methods should cite their source in the module docstring.
3. **Tests stay green.** `pytest` must pass. New statistical code needs a test that
   checks it against a known/analytic case.
4. **Honesty over hype.** This project's value is its restraint. Do not add a
   "strategy that beats them all"- that defeats the point.

## Development setup

```bash
git clone https://github.com/bhavishy2801/AlphaAudit.git
cd AlphaAudit
pip install -e ".[dev]"      # editable install + test deps
pytest                       # run the suite
python run_all.py            # regenerate outputs
cd dashboard && npm install && npm run dev
```

## Commit style

This repo follows [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`,`fix:`,`docs:`,`test:`,`refactor:`,`chore:`. Keep commits scoped.

## Pull requests

- Describe *what* changed and *why*,and include before/after numbers if the
  result moved.
- Link the paper for any new statistical method.
- Keep the dashboard build clean (`npm run build` with no type errors).
