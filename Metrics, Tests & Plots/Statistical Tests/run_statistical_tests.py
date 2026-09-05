import os
from pathlib import Path
from statistical_tests_methods import *

#Paths
root_dir = str(Path(__file__).resolve().parents[2])
metrics_dir = os.path.join(root_dir, "Metrics, Tests & Plots", "Metrics")
stats_dir = os.path.join(root_dir, "Metrics, Tests & Plots", "Statistical Tests")
real_world_csv = os.path.join(metrics_dir, "metrics_real_world.csv")
synthetic_csv = os.path.join(metrics_dir, "metrics_synthetic.csv")

qq_output_dir = os.path.join(stats_dir, "QQ_Plots")
os.makedirs(qq_output_dir, exist_ok=True)

alpha = 0.05
p_disapprove_values = [0.01, 0.05, 0.1, 0.15, 0.2]

#Test A SeqPhragmen-anchored cross distance to TaxPhragmen vs within-traditional distances
test_a_rules = ["SeqPhragmen_vs_TaxPhragmen", "PAV_vs_SeqPhragmen", "SeqPhragmen_vs_MES"]

# Test B: MES-anchored -- cross distance to TaxMES vs within-traditional distances
test_b_rules = ["MES_vs_TaxMES", "PAV_vs_MES", "SeqPhragmen_vs_MES"]

tests = {"Test_A_SeqPhragmen": test_a_rules, "Test_B_MES": test_b_rules}

def run_tests_on_df(df, label, tests):
    for test_name, rule_labels in tests.items():
        groups = {rule: get_group_values(df, rule) for rule in rule_labels}
        empty = [rule for rule, values in groups.items() if len(values) == 0]
        if empty:
            print(f"Skipping {label} - {test_name}: no data for {empty}")
            continue

        qq_path = os.path.join(qq_output_dir, f"{label}_{test_name}_qq.png")
        create_qq_plots(groups, qq_path)

        result = run_group_comparison(groups, alpha=alpha)
        print_result(f"{label} - {test_name}", result)

if __name__ == "__main__":
    print("=" * 50)
    print("Real-world data")
    print("=" * 50)
    df_rw = pd.read_csv(real_world_csv, encoding="utf-8")
    run_tests_on_df(df_rw, "realworld", tests)

    print("\n" + "=" * 50)
    print("Synthetic data")
    print("=" * 50)
    df_syn = pd.read_csv(synthetic_csv, encoding="utf-8")
    for p_val in p_disapprove_values:
        df_pd = df_syn[df_syn["p_disapprove"] == p_val]
        run_tests_on_df(df_pd, f"synthetic_pd_{p_val}", tests)