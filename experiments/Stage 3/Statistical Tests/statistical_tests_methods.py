import numpy as np
import pandas as pd
from scipy import stats
import pingouin as pg
import matplotlib.pyplot as plt

#Statistical tests for Hamming distance group comparisons

def get_group_values(df, rule_label, value_col="hamming_distance", dataset_col="dataset", rule_col="rule"):
    #Extracts one Hamming distance value per dataset for a given rule pair label
    sub = df[df[rule_col] == rule_label].drop_duplicates(subset=[dataset_col])
    return sub[value_col].dropna().to_numpy()

def create_qq_plots(groups, out_path):
    # Saves a row of QQ plots, one per group, for a lenient visual normality check
    fig, axes = plt.subplots(1, len(groups), figsize = (4* len(groups), 4))
    if len(groups) == 1:
        axes = [axes]
    for ax, (label, values) in zip(axes, groups.items()):
        stats.probplot(values, dist="norm", plot=ax)
        ax.set_title(label, fontsize = 9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

def run_group_comparison(groups, alpha=0.05):
    # Runs Levene's test, then either ANOVA + Tukey HSD or Welch ANOVA + Games-Howell
    long_df = pd.concat(
        [pd.DataFrame({"group": label, "value": value}) for label, value in groups.items()],
        ignore_index=True,
    )

    levene_stat, levene_p = stats.levene(*groups.values())
    equal_variance = levene_p >alpha

    result = {
        "alpha": alpha,
        "levene_stat": levene_stat,
        "levene_p": levene_p,
        "equal_variance": equal_variance,
    }

    if equal_variance:
       anova = pg.anova(dv="value", between="group", data=long_df, detailed=True)
       p_value = anova["p-unc"].iloc[0] if "p-unc" in anova.columns else anova["p_unc"].iloc[0]
       result["test"] = "ANOVA"
       result["anova_table"] = anova
       result["p_value"] = p_value
       result["posthoc"] = pg.pairwise_tukey(dv="value", between="group", data=long_df) if p_value < alpha else None
    else:
        welch = pg.welch_anova(dv="value", between="group", data=long_df)
        p_value = welch["p-unc"].iloc[0] if "p-unc" in welch.columns else welch["p_unc"].iloc[0]
        result["test"] = "Welch ANOVA"
        result["anova_table"] = welch
        result["p_value"] = p_value
        result["posthoc"] = pg.pairwise_gameshowell(dv="value", between="group", data=long_df) if p_value < alpha else None

    return result

def print_result(test_name, result):
    print(f"\n{test_name}")
    print(f"  Levene's test: stat={result['levene_stat']:.3f}, p={result['levene_p']:.4g} -> "
          f"{'equal' if result['equal_variance'] else 'unequal'} variances")
    print(f"  {result['test']}: p={result['p_value']:.4g}")
    if result["posthoc"] is not None:
        label = "Tukey HSD" if result["test"] == "ANOVA" else "Games-Howell"
        print(f"  Post-hoc ({label}):")
        print(result["posthoc"].to_string(index=False))
    elif result["p_value"] >= result["alpha"]:
        print("  Not significant, no post-hoc performed.")