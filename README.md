# Card Transaction Fraud: Risk Metrics, Cleaning and Detection

An analysis of a real public fraud dataset (283,726 card transactions after cleaning, 473 fraud) built the way a fraud-prevention analytics team would frame it:
define the metrics, clean and audit the data, find where fraud concentrates, then measure how many frauds a fixed review team could catch.

**Scope, plainly:** this is card fraud from 2013, not freight. The method transfers to any fraud-prevention role (metrics, imbalanced data, review capacity, cost trade-offs). The dataset has no card, account or merchant IDs, so it cannot show link analysis or velocity, and its 28 features are anonymized, so I cannot say what drives the model.

## Run it
```
pip install -r requirements.txt
# put creditcard.csv in data/ (see data/README.md)
python src/run_pipeline.py        # about 40 seconds, deterministic
```

## What it does
1. **Data-quality audit in SQL** (`sql/01_dq_checks.sql`): 7 checks with thresholds and severity. Three raise alerts: 1,081 exact duplicate rows (0.38%), 1,825 zero-amount transactions (0.64%), 55 amounts above $5,000.
2. **Cleaning** (`sql/02_clean.sql`): keeps the first copy of each exact duplicate (1,062 legit, 19 fraud removed); zero amounts are kept and flagged because they turned out to matter.
3. **Fraud KPIs in SQL** (`sql/03_kpis.sql`): fraud rate, fraud dollar rate, fraud by amount band, by hour of cycle, quiet versus busy hours, and by hour since start.
4. **Detection at a review budget** (`src/run_pipeline.py`): logistic regression and gradient boosting against a transparent segment-rate baseline, trained on the first 70% of time and tested on the last 30%. Results are reported at fixed review budgets (0.1% to 1% of transactions), with bootstrap confidence intervals.
5. **Cost trade-off:** net benefit under three assumed review costs ($1, $5, $20 per transaction reviewed). The costs are my assumptions, not facts.

## Findings (all from the data; see docs/FINDINGS.md for the numbers)
- Fraud is 16.7 per 10,000 transactions (473 of 283,726), or 23.3 per 10,000 by dollars. Fraud tickets average $123.87 versus $88.41 for legitimate ones.
- **Quiet hours:** the quietest quarter of hours holds 7.1% of transactions and 24.9% of fraud, a fraud rate 4.3 times the rest.
- **Bursts:** 3 of the 48 hours hold 19.7% of all fraud.
- **Zero-dollar transactions** are 0.64% of volume but 5.3% of fraud, a fraud rate 8.3 times the average. They carry no dollar loss themselves.
- Small tickets of $1 to $10 are 28.2% of transactions and 36.4% of fraud.
- **Detection:** on the later 30% of time (131 frauds in 112,280 transactions), logistic regression finds 90 frauds by reviewing 112 transactions (0.1%): 80% precision, 69% recall. At a 0.5% review budget it finds 110 of 131 (84% recall, 95% interval 78% to 90%) at 5.1 alerts per fraud. Gradient boosting is not meaningfully different (intervals overlap).
- **Cost:** at an assumed $20 per review, reviewing 1% of transactions loses money; the best budget is the smallest one tested.

## Limits you should state in an interview
- Two days of 2013 European card data; fraud patterns today are different.
- Only 131 test frauds, so every test figure has wide uncertainty. The intervals show it.
- Anonymized features: I can rank transactions but not explain why.
- No entity IDs, so no velocity, link or account-takeover analysis.
- The "hour of cycle" is hours since the first transaction, because the real start time is not given.
- Removing exact duplicates was a judgment call; some could be genuine retries. I removed them and counted them.
- The review-cost figures are assumptions.
