# Tableau dashboard spec (build from outputs/)
Sources: kpi_summary.csv, fraud_by_hour_of_cycle.csv, fraud_by_hour_since_start.csv, fraud_by_amount_band.csv,
review_budget_curve.csv, net_benefit_by_budget.csv, scored_test_transactions.csv, dq_report.csv.

Three views:
1. **Executive:** KPI strip (fraud rate, fraud dollar rate, recall and precision at the chosen budget), burst timeline from fraud_by_hour_since_start.
2. **Fraud ops:** review-budget parameter that drives precision, recall, alerts per fraud and net benefit; table of flagged transactions from scored_test_transactions.csv.
3. **Data owner:** dq_report status table (PASS or ALERT, severity, threshold), rows removed.

Alert definitions: hourly fraud rate above 3x its average; any High-severity data-quality check over threshold; alerts per fraud above 6.
Put the KPI definitions from FINDINGS.md on a Definitions tab.
