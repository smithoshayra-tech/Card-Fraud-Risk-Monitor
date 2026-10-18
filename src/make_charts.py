"""Build the README charts from the CSV files in outputs/. No raw data needed."""
from pathlib import Path
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT, IMG = ROOT / "outputs", ROOT / "docs" / "images"
IMG.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#9a9a95", "#1b1b1a", "#5a5955"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#cfcfca",
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlecolor": INK, "axes.titlesize": 12, "axes.titlelocation": "left"})

def finish(fig, ax, name, title, sub):
    ax.set_title(title, pad=22)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=MUTED, va="bottom")
    ax.grid(axis="y", color="#e8e8e4", lw=0.8); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(IMG / name, dpi=160, facecolor="white"); plt.close(fig)

# 1. fraud rate by hour: quiet hours highlighted
h = pd.read_csv(OUT / "fraud_by_hour_of_cycle.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
quiet = h.volume_quartile == 1
ax.bar(h.hour_of_cycle[~quiet], h.fraud_rate_bps[~quiet], color=BLUE, width=0.8, label="Busier hours")
ax.bar(h.hour_of_cycle[quiet], h.fraud_rate_bps[quiet], color=ORANGE, width=0.8, label="Quietest quarter of hours")
ax.axhline(16.67, color=INK, lw=1, ls=":"); ax.text(23.4, 19, "overall rate 16.7", ha="right", fontsize=8.5, color=INK)
ax.set_xlabel("Hour of the 24-hour cycle (hours since the first transaction, two days combined)"); ax.set_ylabel("Fraud per 10,000 transactions")
ax.legend(frameon=False, loc="upper right")
finish(fig, ax, "fraud_by_hour.png", "Fraud concentrates in the quietest hours",
       "Quiet hours hold 7% of transactions but 25% of fraud, a rate 4.3 times the rest")

# 2. share of transactions vs share of fraud by amount band
a = pd.read_csv(OUT / "fraud_by_amount_band.csv")
order = ["zero", "under $1", "$1-10", "$10-50", "$50-200", "$200-1000", "$1000+"]
a = a.set_index("amount_band").loc[order].reset_index()
fig, ax = plt.subplots(figsize=(8, 4.2)); x = range(len(a)); w = 0.38
ax.bar([i - w/2 for i in x], a.share_of_all_txns_pct, w, color=BLUE, label="Share of all transactions")
ax.bar([i + w/2 for i in x], a.share_of_all_fraud_pct, w, color=ORANGE, label="Share of all fraud")
ax.set_xticks(list(x)); ax.set_xticklabels(["$0" if o == "zero" else o for o in a.amount_band])
ax.set_ylabel("Percent"); ax.set_xlabel("Transaction amount")
for i, r in a.iterrows():
    if r.amount_band in ("zero", "$1-10"):
        ax.text(i + w/2, r.share_of_all_fraud_pct + 0.8, f"{r.share_of_all_fraud_pct:.1f}%", ha="center", fontsize=8.5, color=INK)
ax.legend(frameon=False, loc="upper right")
finish(fig, ax, "fraud_by_amount.png", "Small and zero-dollar transactions carry more than their share of fraud",
       "Zero-dollar transactions are 0.6% of volume but 5.3% of fraud (8.3 times the average rate)")

# 3. frauds caught per review budget, model vs simple rule
b = pd.read_csv(OUT / "review_budget_curve.csv")
names = {"Logistic regression": ("Risk model", BLUE), "Baseline: quiet hour x amount band": ("Simple rule (quiet hour x amount)", GRAY)}
fig, ax = plt.subplots(figsize=(8, 4.2)); budgets = sorted(b.review_budget_pct.unique()); w = 0.38
for j, (m, (lab, col)) in enumerate(names.items()):
    d = b[b.method == m].set_index("review_budget_pct").loc[budgets]
    xs = [i + (j - 0.5) * w for i in range(len(budgets))]
    ax.bar(xs, d.frauds_caught, w, color=col, label=lab)
    for xv, v in zip(xs, d.frauds_caught): ax.text(xv, v + 2, int(v), ha="center", fontsize=8.5, color=INK)
ax.set_xticks(range(len(budgets)))
reviewed = b[b.method == "Logistic regression"].set_index("review_budget_pct").loc[budgets].reviewed
ax.set_xticklabels([f"{p:g}% of transactions\n({int(n)} reviewed)" for p, n in zip(budgets, reviewed)])
ax.axhline(131, color=INK, lw=1, ls=":"); ax.text(len(budgets) - 0.5, 134, "131 frauds in the test period", ha="right", fontsize=8.5, color=INK)
ax.set_ylim(0, 175); ax.set_ylabel("Frauds caught"); ax.set_xlabel("Review capacity")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.0), ncol=2)
finish(fig, ax, "frauds_caught_by_budget.png", "A review team that checks 1 in 200 transactions catches 84% of fraud",
       "Held-out test period (last 30% of time): 112,280 transactions, 131 frauds")

# 4. net benefit by review budget at three assumed costs
n = pd.read_csv(OUT / "net_benefit_by_budget.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
for c, col in zip([1, 5, 20], [BLUE, ORANGE, GRAY]):
    d = n[n.review_cost_usd == c]
    ax.plot(d.review_budget_pct, d.net_benefit, marker="o", color=col, lw=2, label=f"${c} per review (assumed)")
    ax.text(d.review_budget_pct.iloc[-1] + 0.02, d.net_benefit.iloc[-1], ("-$" if d.net_benefit.iloc[-1] < 0 else "$") + f"{abs(d.net_benefit.iloc[-1]):,.0f}", va="center", fontsize=8.5, color=INK)
ax.set_xlim(0, 1.15); ax.set_xlabel("Review capacity (% of transactions reviewed)"); ax.set_ylabel("Fraud dollars caught minus review cost ($)")
ax.legend(frameon=False, loc="lower left")
finish(fig, ax, "net_benefit.png", "More review is not always better: it depends on what a review costs",
       "Test-period net benefit. The review costs are my assumptions, not measured values")
print("charts written to", IMG)
