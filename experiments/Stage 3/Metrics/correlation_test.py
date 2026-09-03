import pandas as pd
from scipy import stats

metrics_dir = r"C:\Users\paulc\Documents\bachelor-thesis\experiments\Stage 3\Metrics"
df = pd.read_csv(f"{metrics_dir}\\metrics_synthetic.csv")

syn = df[df["method"].isin(["Traditional", "AV", "Tax"])].copy()
rule_order = ["AV", "PAV", "SeqPhragmen", "MES", "TaxPhragmen", "TaxMES"]

print("\ncheck – avg_elected_disapprovals_per_voter (disapprovals among elected candidates, per rule):")
print(f'{"rule":<14}{"n":>5}{"pearson_r":>12}{"p_value":>12}{"spearman_rho":>14}{"p_value":>12}')
for rule in rule_order:
    sub = syn[syn["rule"] == rule].dropna(subset=["avg_elected_disapprovals_per_voter", "p_disapprove"])
    r, p = stats.pearsonr(sub["p_disapprove"], sub["avg_elected_disapprovals_per_voter"])
    rho, ps = stats.spearmanr(sub["p_disapprove"], sub["avg_elected_disapprovals_per_voter"])
    print(f'{rule:<14}{len(sub):>5}{r:>12.4f}{p:>12.2e}{rho:>14.4f}{ps:>12.2e}')


print("\ncheck — avg_disapprovals_per_voter (all disapprovals, rule-independent):")
for rule in rule_order:
    sub = syn[syn["rule"] == rule].dropna(subset=["avg_disapprovals_per_voter", "p_disapprove"])
    r, p = stats.pearsonr(sub["p_disapprove"], sub["avg_disapprovals_per_voter"])
    rho, ps = stats.spearmanr(sub["p_disapprove"], sub["avg_disapprovals_per_voter"])
    print(f'{rule:<14}{len(sub):>5}{r:>12.4f}{p:>12.2e}{rho:>14.4f}{ps:>12.2e}')