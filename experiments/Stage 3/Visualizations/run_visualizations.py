import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from fontTools.subset import subset
from matplotlib.pyplot import title
from scipy.spatial.transform import rotation

#This file generates all metric visualizations for real-world and synthetic datasets

#Configuration

root_dir = r"C:\Users\paulc\Documents\bachelor-thesis"
metrics_dir = os.path.join(root_dir, "experiments", "Stage 3", "Metrics")
plots_dir = os.path.join(root_dir, "experiments", "Stage 3", "Visualizations", "Plots")
os.makedirs(plots_dir, exist_ok=True)

rw_csv = os.path.join(metrics_dir, "metrics_real_world.csv")
syn_csv = os.path.join(metrics_dir, "metrics_synthetic.csv")

#Color and ordering config
rule_colors = {
    "PAV": "#2196F3",
    "SeqPhragmen": "#4CAF50",
    "MES": "#FF9800",
    "TaxPhragmen": "#9C27B0",
    "TaxMES": "#F44336",
}

rule_order = ["PAV", "SeqPhragmen", "MES", "TaxPhragmen", "TaxMES"]
trad_rules = ["PAV", "SeqPhragmen", "MES"]
tax_rules = ["TaxPhragmen", "TaxMES"]

hamming_pairs = ["PAV_vs_SeqPhragmen", "PAV_vs_MES", "SeqPhragmen_vs_MES", "PAV_vs_TaxMES", "SeqPhragmen_vs_TaxPhragmen", "MES_vs_TaxMES"]

#Seaborn style parameters
sns.set(style="whitegrid", font_scale=1.1)
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"

def save(fig, name):
    path = os.path.join(plots_dir, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {name}")


#Load metrics data
#All metrics
rw_all = pd.read_csv(rw_csv, encoding="utf-8")
syn_all = pd.read_csv(syn_csv, encoding="utf-8")

#Per rule subset excluding hamming rows
rw = rw_all[rw_all["method"].isin(["Traditional", "Tax"])].copy()
syn = syn_all[syn_all["method"].isin(["Traditional", "Tax"])].copy()

#Hamming subsets
rw_hamming_trad = rw_all[rw_all["method"] == "Hamming_traditional"].copy()
rw_hamming_cross = rw_all[rw_all["method"] == "Cross-Hamming"].copy()
syn_hamming_trad = syn_all[syn_all["method"] == "Hamming_Traditional"].copy()
syn_hamming_cross = syn_all[syn_all["method"] == "Cross_Hamming"].copy()

#Shortens real world dataset names for readability
def shorten(name):
    return name[:28] + "..." if len(name) > 28 else name

rw["dataset_short"] = rw["dataset"].apply(shorten)
rw_hamming_trad["dataset_short"] = rw_hamming_trad["dataset"].apply(shorten)
rw_hamming_cross["dataset_short"] = rw_hamming_cross["dataset"].apply(shorten)


#Real world datasets plots

print("\n=== Real World plots ===")

#1 Committee size by rule --> bar chart
fig, ax = plt.subplots(figsize=(13, 5))
plot_df = rw.groupby(["dataset_short", "rule"])["committee_size"].mean().reset_index()
plot_df["rule"] = pd.Categorical(plot_df["rule"], categories=rule_order, ordered=True)
plot_df = plot_df.sort_values("rule")

sns.barplot(data=plot_df, x="dataset_short", y="committee_size", hue="rule", palette = rule_colors, ax=ax)
ax.set_title("Committee Size by Rule - Real World Datasets")
ax.set_xlabel("")
ax.set_ylabel("Committee Size")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax.legend(title="Rule", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "rw1_committee_size.png")


#2 Elected vs Best Non-Elected Net Score --> group bar
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, col, title in zip(axes, ["elected_mean_net_score", "best_non_elected_score"], ["Mean Net Score - Elected Candidates", "Best Non-Elected Candidate Net Score"]):
    sub = rw.dropna(subset=[col])
    sub["rule"] = pd.Categorical(sub["rule"], categories=rule_order, ordered=True)
    sns.boxplot(data=sub, x="rule", y=col, palette=rule_colors, ax=ax, order=rule_order)
    ax.set_title(title)
    ax.set_xlabel("Rule")
    ax.set_ylabel("Net Score")
    ax.set_yscale("log")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
fig.suptitle("Net Scores - Real-World Datasets", fontsize=13, y=1.02)
save(fig, "rw2_net_scores.png")


#3 Gini vs Mean Utility --> scatter
fig, ax = plt.subplots(figsize=(9, 6))
for rule in rule_order:
    sub = rw[rw["rule"] == rule].dropna(subset=["gini_coefficient", "mean_utility"])
    ax.scatter(sub["mean_utility"], sub["gini_coefficient"], label=rule, color=rule_colors[rule], alpha=0.75, s=60, edgecolors="white", linewidths=0.5)
ax.set_xscale("log")
ax.set_xlabel("Mean Voter Utility (log scale)")
ax.set_ylabel("Gini Coefficient")
ax.set_title("Equity vs. Efficiency - Real-World Datasets")
ax.legend(title="Rule")
save(fig, "rw3_gini_vs_utility.png")


#4 Cross-Hamming distance (traditional vs tax counterparts)
fig, ax = plt.subplots(figsize=(13, 5))
cross_pairs = ["PAV_vs_TaxMES", "SeqPhragmen_vs_TaxPhragmen", "MES_vs_TaxMES"]
pair_colors = {
    "PAV_vs_TaxMES": "#2196F3",
    "SeqPhragmen_vs_TaxPhragmen": "#4CAF50",
    "MES_vs_TaxMES": "#FF9800",
}
sub = rw_hamming_cross[rw_hamming_cross["rule"].isin(cross_pairs)]
sns.barplot(data=sub, x="dataset_short", y="hamming_distance", hue="rule", palette=pair_colors, ax=ax)
ax.set_title("Hamming Distance: Traditional vs. Tax Counterparts - Real World Data")
ax.set_xlabel("")
ax.set_ylabel("Hamming Distance")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax.legend(title="Pair", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "rw4_cross_hamming.png")


#5 Within traditional methods hamming distance
fig, ax = plt.subplots(figsize=(13, 5))
trad_pairs = ["PAV_vs_SeqPhragmen", "PAV_vs_MES", "SeqPhragmen_vs_MES"]
trad_pair_colors = {
    "PAV_vs_SeqPhragmen": "#2196F3",
    "PAV_vs_MES": "#4CAF50",
    "SeqPhragmen_vs_MES": "#FF9800",
}
sub = rw_hamming_trad[rw_hamming_trad["rule"].isin(trad_pairs)]
sns.barplot(data=sub, x="dataset_short", y="hamming_distance", hue="rule", palette=trad_pair_colors, ax=ax)
ax.set_title("Hamming Distance: Within Traditional Methods - Real World Data")
ax.set_xlabel("")
ax.set_ylabel("Hamming Distance")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax.legend(title="Pair", bbox_to_anchor=(1.01, 1), loc="upper left")
save(fig, "rw5_trad_hamming.png")


#6 Disapproval avoidance = average elected disapproval per voter, by rule
fig, ax = plt.subplots(figsize=(9, 5))
sub = rw.dropna(subset=["avg_elected_disapprovals_per_voter"])
sub["rule"] = pd.Categorical(sub["rule"], categories=rule_order, ordered=True)
sns.boxplot(data=sub, x="rule", y="avg_elected_disapprovals_per_voter", palette=rule_colors, ax=ax, order=rule_order)
ax.set_title("Disapproval Avoidance - Real World Datasets\n(Average Elected Candidates Disapproved per Voter)")
ax.set_xlabel("Rule")
ax.set_ylabel("Average Disapproved Elected Candidates per Voter")
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
save(fig, "rw6_disapproval_avoidance.png")


#7 Fraction of voters with negative utility by rule
fig, ax = plt.subplots(figsize=(9, 5))
sub = rw.dropna(subset=["frac_negative"])
sub["rule"] = pd.Categorical(sub["rule"], categories=rule_order, ordered=True)
sns.boxplot(data=sub, x="rule", y="frac_negative", palette=rule_colors, ax=ax, order=rule_order)
ax.set_title("Fraction of Voters with Negative Utility - Real-World Data")
ax.set_xlabel("Rule")
ax.set_ylabel("Fraction of Voters")
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
save(fig, "rw7_negative_utility.png")



#Plots on synthetic data

print("\n === Synthetic Data Plots")

pd_values = sorted(syn["p_disapprove"].unique())

#1 Committee size compared to p_disapprove --> line plot per rule
plt.close("all")
fig, ax1 = plt.subplots(figsize=(9, 5))
size_df = syn.groupby(["p_disapprove", "rule"])["committee_size"].mean().reset_index()
# Single reference line for all traditional methods
trad_sub = size_df[size_df["rule"] == "PAV"]
ax1.plot(trad_sub["p_disapprove"], trad_sub["committee_size"],
         marker="o", label="PAV / SeqPhragmen / MES",
         color="#2196F3", linewidth=2)
# Tax methods
for rule in tax_rules:
    sub = size_df[size_df["rule"] == rule]
    ax1.plot(sub["p_disapprove"], sub["committee_size"],
             marker="o", label=rule,
             color=rule_colors[rule], linewidth=2)
ax1.set_ylim(0, 11)
ax1.set_title("Mean Committee Size vs. p_disapprove - Synthetic Data")
ax1.set_xlabel("p_disapprove")
ax1.set_ylabel("Mean Committee Size")
ax1.set_xticks(pd_values)
ax1.legend(title="Rule")
save(fig, "syn1_committee_size_vs_pd.png")


#2 Cross-Hamming distance vs p_disapprove --> line plot
fig, ax = plt.subplots(figsize=(9, 5))
cross_colors = {
    "PAV_vs_TaxMES": "#2196F3",
    "SeqPhragmen_vs_TaxPhragmen": "#4CAF50",
    "MES_vs_TaxMES": "#FF9800",
}
hdf = syn_hamming_cross.groupby(["p_disapprove", "rule"])["hamming_distance"].mean().reset_index()
for pair in cross_colors:
    sub = hdf[hdf["rule"] == pair]
    ax.plot(sub["p_disapprove"], sub["hamming_distance"], marker="o", label=pair, color=cross_colors[pair], linewidth=2)
ax.set_title("Cross-Hamming Distance vs. p_disapprove\n(Traditional vs. Tax Counterparts)")
ax.set_xlabel("p_disapprove")
ax.set_ylabel("Mean Hamming Distance")#
ax.set_xticks(pd_values)
ax.legend(title="Pair")
save(fig, "syn2_cross_hamming_vs_pd.png")


#3 Gini coefficient vs mean utility --> scatter, by model type
models = syn["model"].dropna().unique()
n_models = len(models)
fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5), sharey=True)
if n_models == 1:
    axes = [axes]
for ax, model in zip(axes, sorted(models)):
    sub = syn[(syn["model"] == model)].dropna(subset=["gini_coefficient", "mean_utility"])
    for rule in rule_order:
        r = sub[sub["rule"] == rule]
        ax.scatter(r["mean_utility"], r["gini_coefficient"], label=rule, color=rule_colors[rule], alpha=0.5, s=30, edgecolors="white", linewidth=0.3)
    ax.set_title(model)
    ax.set_xlabel("Mean Voter Utility")
    ax.set_ylabel("Gini Coefficient" if ax == axes[0] else "")
handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=rule_colors[r], markersize=8, label=r) for r in rule_order]
fig.legend(handles=handles, title="Rule", bbox_to_anchor=(1.01, 0.5), loc="center left")
fig.suptitle("Equity vs. Efficiency by Model Type - Synthetic Data", fontsize=13)
save(fig, "syn3_gini_vs_utility_by_model.png")


#4 Gini coefficient vs p_disapprove --> line plot per rule
fig, ax = plt.subplots(figsize=(9, 5))
gini_df = syn.dropna(subset=["gini_coefficient"]).groupby(["p_disapprove", "rule"])["gini_coefficient"].mean().reset_index()
for rule in rule_order:
    sub = gini_df[gini_df["rule"] == rule]
    ax.plot(sub["p_disapprove"], sub["gini_coefficient"], marker="o", label=rule, color=rule_colors[rule], linewidth=2)
ax.set_title("Mean Gini Coefficient vs. p_disapprove - Synthetic Data")
ax.set_xlabel("p_disapprove")
ax.set_ylabel("Gini Coefficient")
ax.set_xticks(pd_values)
ax.legend(title="Rule")
save(fig, "syn4_gini_vs_pd.png")


#5 Voter utility boxplots per rule, faceted by p_disapprove
#Using mean utility per dataset as a proxy
fig, axes5 = plt.subplots(1, len(pd_values), figsize=(4 * len(pd_values), 5), sharey=True)
for ax, p in zip(axes5, pd_values):
    sub = syn[syn["p_disapprove"] == p].dropna(subset=["mean_utility"])
    sub["rule"] = pd.Categorical(sub["rule"], categories=rule_order, ordered=True)
    sns.boxplot(data=sub, x="rule", y="mean_utility", palette=rule_colors, ax=ax, order=rule_order)
    ax.set_title(f"pd={p}")
    ax.set_xlabel("")
    ax.set_ylabel("Mean Voter Utility" if ax == axes5[0] else "")
    ax.set_xticklabels(rule_order, rotation=45, ha="right", fontsize=8)
fig.suptitle("Mean Voter Utility by Rule and p_disapprove - Synthetic Data", fontsize=13)
save(fig, "syn5_utility_boxplots_by_pd.png")


#6 Fraction of voters with negative utility vs p_disapprove
fig, ax = plt.subplots(figsize=(9, 5))
neg_df = syn.dropna(subset=["frac_negative"]).groupby(["p_disapprove", "rule"])["frac_negative"].mean().reset_index()
for rule in rule_order:
    sub = neg_df[neg_df["rule"] == rule]
    ax.plot(sub["p_disapprove"], sub["frac_negative"], marker="o", label=rule, color=rule_colors[rule], linewidth=2)
ax.set_title("Fraction of Voters with Negative Utility vs. p_disapprove")
ax.set_xlabel("p_disapprove")
ax.set_ylabel("Fraction of Voters")
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
ax.set_xticks(pd_values)
ax.legend(title="Rule")
save(fig, "syn6_neg_utility_vs_pd.png")


#7 Disapproval avoidance vs p_disapprove
fig, ax = plt.subplots(figsize=(9, 5))
da_df = syn.dropna(subset=["avg_elected_disapprovals_per_voter"]).groupby(["p_disapprove", "rule"])["avg_elected_disapprovals_per_voter"].mean().reset_index()
for rule in rule_order:
    sub = da_df[da_df["rule"] == rule]
    ax.plot(sub["p_disapprove"], sub["avg_elected_disapprovals_per_voter"], marker="o", label=rule, color=rule_colors[rule], linewidth=2)
ax.set_title("Disapproval Avoidance vs. p_disapprove - Synthetic Data\n(Avg. Elected Candidates Disapproved per Voter)")
ax.set_xlabel("p_disapprove")
ax.set_ylabel("Avg. Disapproved Elected Candidates per Voter")
ax.set_xticks(pd_values)
ax.legend(title="Rule")
save(fig, "syn7_disapproval_avoidance_vs_pd.png")


#8 Within traditional methods Hamming vs p_disapprove
fig, ax = plt.subplots(figsize=(9, 5))
trad_colors = {
    "PAV_vs_SeqPhragmen": "#2196F3",
    "PAV_vs_MES": "#4CAF50",
    "SeqPhragmen_vs_MES": "#FF9800",
}
hdf_trad = syn_hamming_trad.groupby(["p_disapprove", "rule"])["hamming_distance"].mean().reset_index()
for pair in trad_colors:
    sub = hdf_trad[hdf_trad["rule"] == pair]
    ax.plot(sub["p_disapprove"], sub["hamming_distance"], marker="o", label=pair, color=trad_colors[pair], linewidth=2)
ax.set_title("Within Traditional Methods Hamming Distance vs. p_disapprove - Synthetic Data")
ax.set_xlabel("p_disapprove")
ax.set_ylabel("Mean Hamming Distance")
ax.set_xticks(pd_values)
ax.legend(title="Pair")
save(fig, "syn8_trad_hamming_vs_pd.png")


#9 Net score, elected mean vs p_disapprove by model
fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5), sharey=True)
if n_models == 1:
    axes = [axes]
for ax, model in zip(axes, sorted(models)):
    sub = syn[(syn["model"] == model)].dropna(subset=["elected_mean_net_score"])
    ns_df = sub.groupby(["p_disapprove", "rule"])["elected_mean_net_score"].mean().reset_index()
    for rule in rule_order:
        r = ns_df[ns_df["rule"] == rule]
        ax.plot(r["p_disapprove"], r["elected_mean_net_score"], marker="o", label=rule, color=rule_colors[rule], linewidth=2)
    ax.set_title(model)
    ax.set_xlabel("p_disapprove")
    ax.set_ylabel("Mean Elected Net Score" if ax == axes[0] else "")
    ax.set_xticks(pd_values)
handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=rule_colors[r], markersize=8, label=r) for r in rule_order]
fig.legend(handles=handles, title="Rule", bbox_to_anchor=(1.01, 0.5), loc="center left")
fig.suptitle("Mean Elected Net Score vs. p_disapprove by Model - Synthetic Data", fontsize=13)
save(fig, "syn9_net_score_vs_pd_by_model.png")



print(f"\nAll plots saved to: {plots_dir}")

