"""Real data: ULB / Worldline credit card fraud dataset (284,807 card transactions over two days, Sept 2013, 492 fraud).
Steps: load -> SQL data-quality checks -> clean -> SQL fraud KPIs -> time-based model comparison at review budgets
-> dollar-based net benefit -> dashboard-ready extracts."""
import sqlite3, numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import average_precision_score, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
DB, OUT, SQL = ROOT / "data" / "fraud.db", ROOT / "outputs", ROOT / "sql"
OUT.mkdir(exist_ok=True)
SPLIT_FRACTION = 0.70                  # first 70% of time trains, last 30% tests
BUDGETS = [0.001, 0.0025, 0.005, 0.01] # share of test transactions a review team can check
REVIEW_COSTS = [1, 5, 20]              # ASSUMED cost in $ to review one flagged transaction (sensitivity)
V = [f"V{i}" for i in range(1, 29)]

# alert if failing share is above the threshold
THRESHOLDS = {"exact duplicate rows": (0.001, "High"), "missing values in any column": (0.0, "High"),
              "Class not 0 or 1": (0.0, "High"), "negative Amount": (0.0, "High"),
              "zero Amount": (0.001, "Medium"), "Amount above 5000": (0.0001, "Low"),
              "Time goes backwards": (0.0, "High")}

def run_sql(con, name): con.executescript((SQL / name).read_text())

def budget_table(y, amt, score, method):
    n, rows = len(y), []
    order = np.argsort(-score, kind="stable")
    for b in BUDGETS:
        k = int(round(n * b)); top = order[:k]
        caught = y[top].sum()
        rows.append(dict(method=method, review_budget_pct=b * 100, reviewed=k, frauds_caught=int(caught),
                         precision=caught / k, recall=caught / y.sum(),
                         dollar_recall=amt[top][y[top] == 1].sum() / amt[y == 1].sum(),
                         alerts_per_fraud=k / max(caught, 1), fraud_amount_caught=amt[top][y[top] == 1].sum()))
    return rows

def main():
    if DB.exists(): DB.unlink()
    con = sqlite3.connect(DB)
    pd.read_csv(ROOT / "data" / "creditcard.csv").to_sql("txns_raw", con, index=False)

    dq = pd.read_sql((SQL / "01_dq_checks.sql").read_text(), con)
    dq["failing_share"] = dq.failing_rows / dq.total_rows
    dq["threshold"] = dq.check_name.map(lambda n: THRESHOLDS[n][0]); dq["severity"] = dq.check_name.map(lambda n: THRESHOLDS[n][1])
    dq["status"] = np.where(dq.failing_share > dq.threshold, "ALERT", "PASS")
    dq.to_csv(OUT / "dq_report.csv", index=False); dq[dq.status == "ALERT"].to_csv(OUT / "dq_alerts.csv", index=False)

    run_sql(con, "02_clean.sql")
    removed = pd.read_sql("SELECT Class, COUNT(*) AS rows_removed, ROUND(SUM(Amount),2) AS amount FROM txns_removed GROUP BY Class", con)
    removed.to_csv(OUT / "rows_removed.csv", index=False)
    run_sql(con, "03_kpis.sql")
    for t in ["kpi_summary", "fraud_by_amount_band", "fraud_by_hour_of_cycle", "quiet_vs_busy", "fraud_by_hour_since_start"]:
        pd.read_sql(f"SELECT * FROM {t}", con).to_csv(OUT / f"{t}.csv", index=False)

    df = pd.read_sql("SELECT * FROM txns ORDER BY Time, txn_id", con)
    df["log_amount"] = np.log1p(df.Amount)
    ang = 2 * np.pi * df.hour_of_cycle / 24; df["hour_sin"], df["hour_cos"] = np.sin(ang), np.cos(ang)
    feats = V + ["log_amount", "hour_sin", "hour_cos"]
    cut = df.Time.max() * SPLIT_FRACTION
    tr, te = df[df.Time <= cut], df[df.Time > cut]
    y, amt = te.Class.values, te.Amount.values

    models = {"Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
              "Gradient boosting": HistGradientBoostingClassifier(max_depth=4, learning_rate=0.06, max_iter=250,
                                                                  class_weight="balanced", random_state=42)}
    scores = {}
    for name, m in models.items():
        m.fit(tr[feats], tr.Class); scores[name] = m.predict_proba(te[feats])[:, 1]
    # transparent baseline an analyst could build in SQL: fraud rate by (quiet hour x amount band), learned on the training period only
    quiet = set(pd.read_sql("SELECT hour_of_cycle FROM fraud_by_hour_of_cycle WHERE volume_quartile = 1", con).hour_of_cycle)
    seg = lambda d: d.hour_of_cycle.isin(quiet).astype(str) + "|" + d.amount_band
    rate = tr.groupby(seg(tr)).Class.agg(["sum", "count"])
    prior = tr.Class.mean(); rate["r"] = (rate["sum"] + 20 * prior) / (rate["count"] + 20)   # smoothed
    scores["Baseline: quiet hour x amount band"] = seg(te).map(rate["r"]).fillna(prior).values

    bt = pd.DataFrame([r for n, s in scores.items() for r in budget_table(y, amt, s, n)])
    bt.to_csv(OUT / "review_budget_curve.csv", index=False)
    rng = np.random.default_rng(42); ci = []
    for name, s in scores.items():
        rec = []
        k = int(round(len(y) * 0.005)); idx = np.arange(len(y))
        for _ in range(300):
            b = rng.choice(idx, len(y)); yb, sb = y[b], s[b]
            top = np.argsort(-sb, kind="stable")[:k]; rec.append(yb[top].sum() / max(yb.sum(), 1))
        ci.append(dict(method=name, pr_auc=average_precision_score(y, s),
                       recall_at_0_5pct_budget=bt[(bt.method == name) & (bt.review_budget_pct == 0.5)].recall.iloc[0],
                       recall_ci_low=np.percentile(rec, 2.5), recall_ci_high=np.percentile(rec, 97.5)))
    met = pd.DataFrame(ci); met["test_transactions"] = len(te); met["test_frauds"] = int(y.sum())
    met["base_rate_pct"] = y.mean() * 100; met.to_csv(OUT / "model_metrics.csv", index=False)

    # net benefit under assumed review costs, best model
    best = met.sort_values("pr_auc", ascending=False).iloc[0].method
    nb = []
    for c in REVIEW_COSTS:
        for r in bt[bt.method == best].itertuples():
            nb.append(dict(method=best, review_cost_usd=c, review_budget_pct=r.review_budget_pct,
                           fraud_amount_caught=r.fraud_amount_caught, review_cost_total=r.reviewed * c,
                           net_benefit=r.fraud_amount_caught - r.reviewed * c))
    pd.DataFrame(nb).to_csv(OUT / "net_benefit_by_budget.csv", index=False)

    sc = te[["txn_id", "Time", "hour_of_cycle", "Amount", "amount_band", "Class"]].copy()
    sc["risk_score"] = scores[best]; sc["risk_rank_pct"] = sc.risk_score.rank(pct=True, ascending=False)
    sc["flagged_at_0_5pct_budget"] = (sc.risk_rank_pct <= 0.005).astype(int)
    sc.to_csv(OUT / "scored_test_transactions.csv", index=False)

    plt.figure(figsize=(6.4, 4.2))
    for name, s in scores.items():
        p, r, _ = precision_recall_curve(y, s); plt.plot(r, p, label=name)
    plt.axhline(y.mean(), ls=":", c="gray", label="Base rate"); plt.xlabel("Recall"); plt.ylabel("Precision")
    plt.title("Out-of-time test set (last 30% of the two days)"); plt.legend(fontsize=8); plt.tight_layout()
    plt.savefig(OUT / "pr_curve.png", dpi=150); plt.close()

    print(pd.read_sql("SELECT * FROM kpi_summary", con).T.to_string()); print(dq[["check_name","failing_rows","failing_share","status"]].to_string(index=False))
    print(removed.to_string(index=False)); print(pd.read_sql("SELECT * FROM quiet_vs_busy", con).to_string(index=False))
    print(pd.read_sql("SELECT * FROM fraud_by_amount_band", con).to_string(index=False))
    print(f"train {len(tr):,} (fraud {tr.Class.sum()}), test {len(te):,} (fraud {int(y.sum())})")
    print(met.round(3).to_string(index=False)); print(bt[bt.review_budget_pct.isin([0.1,0.5])].round(3).to_string(index=False))
    print(pd.DataFrame(nb).round(0).to_string(index=False))

if __name__ == "__main__":
    main()
