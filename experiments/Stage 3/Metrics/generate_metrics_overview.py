import os
import pandas as pd

root_dir = r"C:\Users\paulc\Documents\bachelor-thesis"
metrics_dir = os.path.join(root_dir, "experiments", "Stage 3", "Metrics")

rw_csv = os.path.join(metrics_dir, "metrics_real_world.csv")
syn_csv = os.path.join(metrics_dir, "metrics_synthetic.csv")
output_path = os.path.join(metrics_dir, "metrics_overview.txt")

rw_all = pd.read_csv(rw_csv, encoding="utf-8")
syn_all = pd.read_csv(syn_csv, encoding="utf-8")

rw = rw_all[rw_all["method"].isin(["Traditional", "Tax"])].copy()
syn = syn_all[syn_all["method"].isin(["Traditional", "Tax"])].copy()

metric_cols = [
    "committee_size",
    "elected_mean_net_score", "elected_min_net_score", "elected_max_net_score",
    "non_elected_mean_net_score", "best_non_elected_score",
    "mean_utility", "median_utility",
    "frac_zero_or_negative", "frac_negative",
    "gini_coefficient",
    "avg_disapprovals_per_voter", "avg_elected_disapprovals_per_voter",
]

rule_order = ["PAV", "SeqPhragmen", "MES", "TaxPhragmen", "TaxMES"]

lines = []


#Real-world overview

lines.append("=" * 70)
lines.append("METRICS OVERVIEW — REAL-WORLD DATASETS")
lines.append(f"Datasets: {rw['dataset'].nunique()} | Rules: {rw['rule'].nunique()} | Total rows: {len(rw)}")
lines.append("=" * 70)

lines.append("")
lines.append("--- Per-rule summary (mean ± std | min | median | max) ---")
lines.append("")

for rule in rule_order:
    sub = rw[rw["rule"] == rule]
    lines.append(f"Rule: {rule}  (n={len(sub)} datasets)")
    lines.append("-" * 50)
    for col in metric_cols:
        vals = sub[col].dropna()
        if len(vals) == 0:
            continue
        lines.append(f"  {col:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  median={vals.median():.4f}  max={vals.max():.4f}")
    lines.append("")

lines.append("")
lines.append("--- Per-dataset summary (all rules combined) ---")
lines.append("")
for ds in sorted(rw["dataset"].unique()):
    sub = rw[rw["dataset"] == ds]
    lines.append(f"Dataset: {ds}")
    lines.append("-" * 50)
    for col in metric_cols:
        vals = sub[col].dropna()
        if len(vals) == 0:
            continue
        lines.append(f"  {col:<42} mean={vals.mean():.4f}  min={vals.min():.4f}  max={vals.max():.4f}")
    lines.append("")

lines.append("--- Hamming distance summary (real-world) ---")
lines.append("")
rw_h = rw_all[~rw_all["method"].isin(["Traditional", "Tax"])].dropna(subset=["hamming_distance"])
for pair in sorted(rw_h["rule"].dropna().unique()):
    vals = rw_h[rw_h["rule"] == pair]["hamming_distance"]
    lines.append(f"  {pair:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  median={vals.median():.4f}  max={vals.max():.4f}")


#Synthetic Overview

lines.append("")
lines.append("")
lines.append("=" * 70)
lines.append("METRICS OVERVIEW — SYNTHETIC DATASETS")
lines.append(f"Datasets: {syn['dataset'].nunique()} | p_disapprove levels: {syn['p_disapprove'].nunique()} | Rules: {syn['rule'].nunique()} | Total rows: {len(syn)}")
lines.append("=" * 70)

lines.append("")
lines.append("--- Per-rule summary across all p_disapprove and datasets ---")
lines.append("")
for rule in rule_order:
    sub = syn[syn["rule"] == rule]
    lines.append(f"Rule: {rule}  (n={len(sub)})")
    lines.append("-" * 50)
    for col in metric_cols:
        vals = sub[col].dropna()
        if len(vals) == 0:
            continue
        lines.append(f"  {col:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  median={vals.median():.4f}  max={vals.max():.4f}")
    lines.append("")

lines.append("")
lines.append("--- Per-rule breakdown by p_disapprove ---")
lines.append("")
for p in sorted(syn["p_disapprove"].unique()):
    lines.append(f"p_disapprove = {p}")
    lines.append("=" * 50)
    for rule in rule_order:
        sub = syn[(syn["rule"] == rule) & (syn["p_disapprove"] == p)]
        lines.append(f"  Rule: {rule}  (n={len(sub)})")
        for col in metric_cols:
            vals = sub[col].dropna()
            if len(vals) == 0:
                continue
            lines.append(f"    {col:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  median={vals.median():.4f}  max={vals.max():.4f}")
        lines.append("")
    lines.append("")

lines.append("--- Per-rule breakdown by model type ---")
lines.append("")
for model in sorted(syn["model"].dropna().unique()):
    lines.append(f"Model: {model}")
    lines.append("=" * 50)
    for rule in rule_order:
        sub = syn[(syn["rule"] == rule) & (syn["model"] == model)]
        lines.append(f"  Rule: {rule}  (n={len(sub)})")
        for col in metric_cols:
            vals = sub[col].dropna()
            if len(vals) == 0:
                continue
            lines.append(f"    {col:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  median={vals.median():.4f}  max={vals.max():.4f}")
        lines.append("")
    lines.append("")

lines.append("--- Hamming distance summary (synthetic, by p_disapprove) ---")
lines.append("")
syn_h = syn_all[~syn_all["method"].isin(["Traditional", "Tax"])].dropna(subset=["hamming_distance"])
for p in sorted(syn_h["p_disapprove"].dropna().unique()):
    lines.append(f"p_disapprove = {p}")
    sub_p = syn_h[syn_h["p_disapprove"] == p]
    for pair in sorted(sub_p["rule"].dropna().unique()):
        vals = sub_p[sub_p["rule"] == pair]["hamming_distance"]
        lines.append(f"  {pair:<42} mean={vals.mean():.4f}  std={vals.std():.4f}  min={vals.min():.4f}  max={vals.max():.4f}")
    lines.append("")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Saved to: {output_path}")
