import csv
import os
import json
import sys
from datetime import datetime
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


def load_transactions(csv_file: str = "transactions.csv") -> list[dict]:
    transactions = []
    if not Path(csv_file).exists():
        return transactions
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["amount"] = float(row["amount"])
                row["type"]   = row["type"].strip().upper()
                transactions.append(row)
            except (ValueError, KeyError):
                continue
    return transactions


def save_transaction(data: dict, csv_file: str = "transactions.csv"):
    file_exists = Path(csv_file).exists()
    next_id = 1
    if file_exists:
        rows = load_transactions(csv_file)
        if rows:
            next_id = max(int(r["id"]) for r in rows) + 1

    data["id"] = next_id
    fieldnames = ["id", "date", "category", "description", "amount", "type"]
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    return next_id


def compute_summary(transactions: list[dict], month: str = "") -> dict:
    income   = 0.0
    expenses = 0.0
    by_cat   = defaultdict(float)
    by_month = defaultdict(lambda: {"income": 0.0, "expense": 0.0})

    for t in transactions:
        m = t["date"][:7]
        if month and m != month:
            continue
        if t["type"] == "INCOME":
            income += t["amount"]
            by_month[m]["income"] += t["amount"]
        else:
            expenses += t["amount"]
            by_cat[t["category"]] += t["amount"]
            by_month[m]["expense"] += t["amount"]

    return {
        "total_income":   income,
        "total_expenses": expenses,
        "net_balance":    income - expenses,
        "by_category":    dict(sorted(by_cat.items(), key=lambda x: -x[1])),
        "by_month":       dict(sorted(by_month.items())),
    }


PALETTE = {
    "income":  "#4ade80",
    "expense": "#f87171",
    "accent1": "#60a5fa",
    "accent2": "#a78bfa",
    "accent3": "#fb923c",
    "accent4": "#34d399",
    "accent5": "#f472b6",
    "bg":      "#0f172a",
    "text":    "#e2e8f0",
    "grid":    "#1e293b",
}

# i am so done with this shit

PIE_COLORS = [PALETTE["accent1"], PALETTE["accent2"], PALETTE["accent3"],
              PALETTE["accent4"], PALETTE["accent5"], "#facc15", "#e879f9"]


def _style_ax(ax):
    ax.set_facecolor(PALETTE["bg"])
    ax.tick_params(colors=PALETTE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["grid"])
    ax.yaxis.grid(True, color=PALETTE["grid"], linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.title.set_color(PALETTE["text"])
    ax.xaxis.label.set_color(PALETTE["text"])
    ax.yaxis.label.set_color(PALETTE["text"])


def plot_category_pie(summary: dict, out_file: str = "chart_categories.png"):
    if not HAS_MATPLOTLIB:
        print("  [skip] skipping pie chart.")
        return
    cats = summary["by_category"]
    if not cats:
        print("  No expense categories to chart.")
        return

    labels = list(cats.keys())
    sizes  = list(cats.values())
    colors = PIE_COLORS[:len(labels)]

    fig, ax = plt.subplots(figsize=(7, 5), facecolor=PALETTE["bg"])
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 2},
        pctdistance=0.78
    )
    for at in autotexts:
        at.set_color(PALETTE["bg"])
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax.legend(wedges, [f"{l}  (${v:,.2f})" for l, v in zip(labels, sizes)],
              loc="lower centre", bbox_to_anchor=(0.5, -0.18),
              ncol=2, frameon=False,
              labelcolor=PALETTE["text"], fontsize=8)

    ax.set_title("Expenses by category", pad=16, fontsize=13, fontweight="bold",
                 color=PALETTE["text"])
    fig.patch.set_facecolor(PALETTE["bg"])
    plt.tight_layout()
    plt.savefig(out_file, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved: {out_file}")


def plot_monthly_bar(summary: dict, out_file: str = "chart_monthly.png"):
    if not HAS_MATPLOTLIB:
        print("  [skip]skipping bar chart.")
        return
    monthly = summary["by_month"]
    if not monthly:
        print("  No monthly data to chart.")
        return

    months   = list(monthly.keys())
    incomes  = [monthly[m]["income"]  for m in months]
    expenses = [monthly[m]["expense"] for m in months]

    x = range(len(months))
    w = 0.35

    fig, ax = plt.subplots(figsize=(max(7, len(months) * 1.2), 4.5),
                           facecolor=PALETTE["bg"])
    ax.bar([i - w/2 for i in x], incomes,  width=w, label="Income",
           color=PALETTE["income"],  alpha=0.9, zorder=3)
    ax.bar([i + w/2 for i in x], expenses, width=w, label="Expenses",
           color=PALETTE["expense"], alpha=0.9, zorder=3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Amount ($)")
    ax.set_title("Monthly Income vs Expenses", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, labelcolor=PALETTE["text"])

    _style_ax(ax)
    fig.patch.set_facecolor(PALETTE["bg"])
    plt.tight_layout()
    plt.savefig(out_file, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved: {out_file}")


def plot_balance_trend(transactions: list[dict], out_file: str = "chart_trend.png"):
    if not HAS_MATPLOTLIB:
        print("  [skip] skipping trend chart.")
        return 
    if not transactions:
        print("  No data for trend chart.")
        return

    sorted_t = sorted(transactions, key=lambda r: r["date"])
    dates, balances = [], []
    running = 0.0
    for t in sorted_t:
        running += t["amount"] if t["type"] == "INCOME" else -t["amount"]
        dates.append(t["date"])
        balances.append(running)

    fig, ax = plt.subplots(figsize=(9, 4), facecolor=PALETTE["bg"])
    ax.plot(dates, balances, color=PALETTE["accent1"], linewidth=2, zorder=3)
    ax.fill_between(range(len(dates)), balances,
                    color=PALETTE["accent1"], alpha=0.15)

    step = max(1, len(dates) // 8)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels(dates[::step], rotation=30, ha="right", fontsize=7)
    ax.axhline(0, color=PALETTE["grid"], linestyle="--", linewidth=0.8)
    ax.set_ylabel("Balance ($)")
    ax.set_title("Running Balance Over Time", fontsize=13, fontweight="bold")

    _style_ax(ax)
    fig.patch.set_facecolor(PALETTE["bg"])
    plt.tight_layout()
    plt.savefig(out_file, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"Chart saved:{out_file}")


def print_report(transactions: list[dict], month: str = ""):
    summary = compute_summary(transactions, month)

    header = "ALL TIME" if not month else month
    width  = 48
    print(f"\n{'-' * width}")
    print(f"  BUDGET REPORT  --  {header}")
    print(f"{'-' * width}")
    print(f"  Total Income:    ${summary['total_income']:>10,.2f}")
    print(f"  Total Expenses:  ${summary['total_expenses']:>10,.2f}")
    net = summary['net_balance']
    sign = "+" if net >= 0 else ""
    print(f"  Net Balance:     {sign}${net:>10,.2f}")
    print(f"{'-' * width}")

    if summary["by_category"]:
        print("\n  Expenses by Category:")
        rows = [(cat, f"${amt:,.2f}") for cat, amt in summary["by_category"].items()]
        if HAS_TABULATE:
            print(tabulate(rows, headers=["Category", "Amount"],
                           tablefmt="rounded_outline", colalign=("left", "right")))
        else:
            for cat, amt in rows:
                print(f"    {cat:<20} {amt:>10}")

    if summary["by_month"]:
        print("\n  Monthly Breakdown:")
        rows = [(m, f"${d['income']:,.2f}", f"${d['expense']:,.2f}",
                 f"${d['income']-d['expense']:,.2f}")
                for m, d in summary["by_month"].items()]
        if HAS_TABULATE:
            print(tabulate(rows, headers=["Month", "Income", "Expense", "Net"],
                           tablefmt="rounded_outline",
                           colalign=("left", "right", "right", "right")))
        else:
            print(f"    {'Month':<10} {'Income':>12} {'Expense':>12} {'Net':>12}")
            for r in rows:
                print(f"    {r[0]:<10} {r[1]:>12} {r[2]:>12} {r[3]:>12}")
    print()
    return summary


def export_json(summary: dict, out_file: str = "budget_summary.json"):
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  JSON summary: {out_file}")


def main():
    csv_file = "transactions.csv"

    if not Path(csv_file).exists():
        print("No transactions.csv found")
        samples = [
            {"date":"2026-01-05","category":"Salary","description":"Monthly salary","amount":5000,"type":"INCOME"},
            {"date":"2026-01-10","category":"Rent","description":"January rent","amount":1200,"type":"EXPENSE"},
            {"date":"2026-01-12","category":"Food","description":"Grocery shopping","amount":180,"type":"EXPENSE"},
            {"date":"2026-01-15","category":"Utilities","description":"Electric bill","amount":95,"type":"EXPENSE"},
            {"date":"2026-01-20","category":"Entertainment","description":"Netflix & Spotify","amount":30,"type":"EXPENSE"},
            {"date":"2026-01-22","category":"Transport","description":"Gas","amount":60,"type":"EXPENSE"},
            {"date":"2026-02-05","category":"Salary","description":"Monthly salary","amount":5000,"type":"INCOME"},
            {"date":"2026-02-07","category":"Freelance","description":"Web project","amount":800,"type":"INCOME"},
            {"date":"2026-02-10","category":"Rent","description":"February rent","amount":1200,"type":"EXPENSE"},
            {"date":"2026-02-14","category":"Food","description":"Valentines dinner","amount":110,"type":"EXPENSE"},
            {"date":"2026-02-18","category":"Health","description":"Gym membership","amount":45,"type":"EXPENSE"},
            {"date":"2026-02-25","category":"Shopping","description":"New laptop bag","amount":75,"type":"EXPENSE"},
            {"date":"2026-03-05","category":"Salary","description":"Monthly salary","amount":5200,"type":"INCOME"},
            {"date":"2026-03-10","category":"Rent","description":"March rent","amount":1200,"type":"EXPENSE"},
            {"date":"2026-03-15","category":"Food","description":"Groceries","amount":200,"type":"EXPENSE"},
            {"date":"2026-03-20","category":"Transport","description":"Car service","amount":150,"type":"EXPENSE"},
        ] # seriously..? 
        for s in samples:
            save_transaction(s, csv_file)
        print(f"  Seeded {len(samples)} sample transactions.\n")

    transactions = load_transactions(csv_file)
    print(f"\n  Loaded {len(transactions)} transactions from {csv_file}")

    summary = print_report(transactions)

    print("  Generating charts")
    os.makedirs("img", exist_ok=True)
    plot_category_pie(summary, "img/chart_categories.png")
    plot_monthly_bar(summary, "img/chart_monthly.png")
    plot_balance_trend(transactions, "img/chart_trend.png")

    export_json(summary, "budget_summary.json")

    print("\n Yay !\n")


if __name__ == "__main__":
    main()

    # i hate python