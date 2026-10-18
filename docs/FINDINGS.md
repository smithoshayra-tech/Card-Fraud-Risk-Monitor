# Findings and KPI definitions

## KPIs (what to track on a fraud dashboard)
| KPI | Definition | Value here |
|---|---|---|
| Fraud rate (bps) | fraud transactions / transactions x 10,000 | 16.67 |
| Fraud dollar rate (bps) | fraud amount / total amount x 10,000 | 23.34 |
| Average fraud ticket | mean Amount where Class = 1 | $123.87 (legit $88.41) |
| Precision at budget | frauds among reviewed / reviewed | 80.4% at 0.1% budget |
| Recall at budget | frauds caught / all frauds in the period | 68.7% at 0.1%, 84.0% at 0.5% |
| Dollar recall at budget | fraud dollars caught / all fraud dollars | 62.2% at 0.1%, 65.9% at 0.5% |
| Alerts per fraud | reviewed / frauds caught | 1.2 at 0.1%, 5.1 at 0.5% |
| Net benefit | fraud dollars caught - review cost x reviewed | depends on assumed cost |
| Data-quality alert count | checks over threshold | 3 of 7 |

## Example OKR (my framing; not Amazon's)
Objective: stop more fraud without growing the review queue.
- KR1: catch 80%+ of fraud transactions while reviewing no more than 0.5% of volume.
- KR2: keep alerts per fraud at 6 or fewer.
- KR3: zero high-severity data-quality alerts open for more than one day.

## What the data says
1. Overall: 473 fraud in 283,726 transactions after removing 1,081 duplicates (19 were fraud).
2. Quiet hours: 118 of 473 frauds (24.9%) fall in the quietest quarter of hours, which hold 7.1% of volume. Fraud rate 58.2 bps versus 13.5 bps elsewhere.
3. Bursts: hours 11, 26 and 7 since start hold 9.1%, 5.7% and 4.9% of all fraud (19.7% in total).
4. Amount: $1-10 transactions are 28.2% of volume and 36.4% of fraud. Zero-dollar transactions have a 138 bps fraud rate (8.3x average). Over $1,000 the rate is 29.4 bps but only 9 frauds.
5. Models (last 30% of time, 131 frauds): PR-AUC 0.742 logistic regression, 0.733 gradient boosting, 0.003 for the segment-rate baseline. The baseline fails because a coarse table cannot rank transactions within a segment.
6. Net benefit: at assumed review costs of $5 and $20 the best budget tested is 0.1%; at $1 it is 1%. At $20, reviewing 1% costs more than the fraud it catches.

## Not tested
Card-level behavior, velocity, device or merchant data, concept drift over months, probability calibration.
