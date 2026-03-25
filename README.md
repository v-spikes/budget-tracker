# Personal Budget Tracker

\---

## Quick Introduction



A project my friends and I decide to do while in the mid-sem break. 

This is a non-profit project and its sole purpose is only to kill time for the authors.

\---

## Quick Start

### 1 · C++ CLI (core engine)

```bash
# Compile (requires g++ with C++17)
g++ -std=c++17 -O2 -o budget\_engine budget\_engine.cpp

# Run
./budget\_engine
```

Features:

* Add income / expenses
* List all transactions
* Summary report (all-time or by month)
* Delete transactions
* Auto-saves to `transactions.csv`

### 2 · Python Analytics

```bash
# Install dependencies
pip install matplotlib pandas tabulate

# Run (reads transactions.csv, seeds sample data if missing)
python3 analytics.py
```

Outputs:

* Terminal report with category \& monthly breakdown
* `chart\_categories.png`  — expense pie chart
* `chart\_monthly.png`     — monthly income vs expense bar chart
* `chart\_trend.png`       — running balance line chart
* `budget\_summary.json`   — machine-readable summary

### 3 · HTML Dashboard

Open `index.html` in any browser — **no server required**.

Features:

* Live KPI cards (income, expenses, net balance, count)
* Add / delete transactions in-browser
* Search \& filter (by type, category, text)
* Running balance trend chart (canvas)
* Category breakdown bars
* Monthly snapshot table
* Export to CSV (compatible with C++ engine)

\---

## CSV Interchange

You can use all three tools on the **same data file**:

```bash
# 1. Use C++ CLI to add transactions
./budget\_engine

# 2. Run Python analytics on the same file
python3 analytics.py

# 3. Open index.html, import/export CSV to sync with browser
```

\---

## Sample Data

Both Python and the HTML dashboard auto-seed 16 sample transactions
across Jan–Mar 2026 if no data file is found.

\---

## Requirements

|Tool|Requirement|
|-|-|
|C++|g++ >= 7 with `-std=c++17`|
|Python|Python >= 3.10, `pip install matplotlib tabulate`|
|HTML|Any modern browser (Chrome, Firefox, Safari, Edge)|

\---



## Credits:

Thanks to [Hoang Anh](https://www.instagram.com/hoaanh.02/) for the png files. 

Thanks to [Johnny](https://www.instagram.com/johnny\_45.1/) for the C++ and HTML codes. 


\---


## The stories behind:

I was motivated to do this as I've just taken a data analytics course, and as an econometrics student, I wanted to try my hand at financial analysis thingy during my midterm break.



