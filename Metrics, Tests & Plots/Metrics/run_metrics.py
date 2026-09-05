import os
import pandas as pd
from pathlib import Path
from metrics_methods import *

#Metric computation for all datasets

#Path setup
root_dir = str(Path(__file__).resolve().parents[2])

polis_data_dir = os.path.join(root_dir, "Data", "Real-World", "openData-master")
polis_results = os.path.join(root_dir, "Results", "Results Real-World")

synthetic_data_dir = os.path.join(root_dir, "Data", "Synthetic Data")
synthetic_results = os.path.join(root_dir, "Results", "Results Synthetic")

p_disapprove_values = [0.01, 0.05, 0.1, 0.15, 0.2]#

output_dir = os.path.join(root_dir, "Metrics, Tests & Plots", "Metrics")
os.makedirs(output_dir, exist_ok=True)


#Helper functions

def load_vote_matrix(csv_path):
    #Loads the vote matrix into a pandas dataframe, candidate_cols as int and voter_ids are preserved
    df = pd.read_csv(csv_path, encoding="utf-8")
    #Identifies candidate columns
    candidate_cols = []
    rename_map = {}
    for col in df.columns:
        try:
            rename_map[col] = int(col)
            candidate_cols.append(int(col))
        except(ValueError, TypeError):
            pass
    df = df.rename(columns=rename_map)
    # Keep only candidate columns (pure integers) plus voter_id if present
    cols_to_keep = candidate_cols[:]
    if "voter_id" in df.columns:
        cols_to_keep = ["voter_id"] + candidate_cols
    df = df[cols_to_keep]
    # Fill possible Nulls with abstain votes
    df[candidate_cols] = df[candidate_cols].fillna(0).astype(int)

    return df, candidate_cols

def get_committees_from_results(results_df):
    #Parses a result dataframe into a dict
    committees = {}
    for _, row in results_df.iterrows():
        rule = row["Rule"]
        candidates = parse_candidates_lists(row["Selected_Candidates"])
        committees[rule] = candidates

    return committees

def find_polis_csv(dataset_path):
    #Finds the main csv in a polis dataset folder
    full_path = os.path.join(dataset_path, "participants-votes.csv")
    if os.path.exists(full_path):
        return full_path
    print(f"  Warning, No participants-votes.csv found in {dataset_path}.")

    return None

#Pol.is data metrics

def compute_realworld_metrics():
    rows = []

    datasets = [d for d in os.listdir(polis_data_dir) if os.path.isdir(os.path.join(polis_data_dir, d))]

    for dataset in sorted(datasets):
        result_dir = os.path.join(polis_results, dataset)
        data_dir = os.path.join(polis_data_dir, dataset)

        trad_path = os.path.join(result_dir, "winning_committees_list.csv")
        tax_path = os.path.join(result_dir, "tax_winning_committees.csv")

        if not os.path.exists(trad_path) or not os.path.exists(tax_path):
            print(f"Skipping {dataset}: missing results files")
            continue

        print(f"Processing polis: {dataset}")

        trad_df = pd.read_csv(trad_path, encoding="utf-8")
        tax_df = pd.read_csv(tax_path, encoding="utf-8")

        trad_committees = get_committees_from_results(trad_df)
        tax_committees = get_committees_from_results(tax_df)
        all_committees = {**trad_committees, **tax_committees}

        #Load vote matrix
        polis_csv = find_polis_csv(data_dir)
        if polis_csv is None:
            print(f"No data csv found for {dataset}, skipping voter metrics.")
            vote_matrix = None
            candidate_cols = []
        else:
            vote_matrix, candidate_cols = load_vote_matrix(polis_csv)
            print(f"  Loaded vote matrix: {len(vote_matrix)} voters, {len(candidate_cols)} candidates.")


        #Net Scores
        net_scores = None
        if vote_matrix is not None:
            net_scores = compute_net_scores(vote_matrix, len(candidate_cols))

        #Hamming distances within traditional methods
        hamming_trad = compute_hamming_matrix(trad_committees)
        #Hamming distances within tax methods
        hamming_tax = compute_hamming_matrix(tax_committees)
        #Cross hamming distance: traditional vs tax
        cross_hamming = compute_cross_hamming(trad_committees, tax_committees)

        #Per Rule Metrics
        for rule, committee in all_committees.items():
            method = "Tax" if rule in tax_committees else ("AV" if rule == "AV" else "Traditional")
            row = {
                "dataset": dataset,
                "method": method,
                "rule": rule,
                "committee_size": len(committee),
            }

            #Net Score Metrics
            if net_scores is not None:
                ns = net_score_summary(net_scores, committee)
                row.update(ns)

                #Voter Utility Metrics
                utilities = compute_voter_utilities(vote_matrix, committee, net_scores)
                row.update(voter_utility_metrics(utilities))

                #Disapproval Metrics
                row["avg_disapprovals_per_voter"] = avg_disapproval_per_voter(vote_matrix)
                row["avg_elected_disapprovals_per_voter"] = disapproval_avoidance(vote_matrix, committee)
            else:
                #If no vote matrix is available then fill with None
                for key in ["elected_mean_net_score", "elected_min_net_score", "elected_max_net_score",
                            "non_elected_mean_net_score", "best_non_elected_score", "best_non_elected_candidate",
                            "mean_utility", "median_utility", "n_zero_or_negative", "frac_zero_or_negative",
                            "n_negative", "frac_negative", "gini_coefficient",
                            "avg_disapprovals_per_voter", "avg_elected_disapprovals_per_voter"]:
                    row[key] = None

            rows.append(row)

        #Hamming summary
        #Within traditional methods
        for r1, r2 in [("PAV", "SeqPhragmen"), ("PAV", "MES"), ("SeqPhragmen", "MES"), ("AV", "PAV"), ("AV", "SeqPhragmen"), ("AV", "MES")]:
            if r1 in trad_committees and r2 in trad_committees:
                rows.append({
                    "dataset": dataset,
                    "method": "Hamming_traditional",
                    "rule": f"{r1}_vs_{r2}",
                    "committee_size": None,
                    **{k: None for k in ["elected_mean_net_score", "elected_min_net_score", "elected_max_net_score",
                                         "non_elected_mean_net_score", "best_non_elected_score",
                                         "best_non_elected_candidate",
                                         "mean_utility", "median_utility", "n_zero_or_negative",
                                         "frac_zero_or_negative",
                                         "n_negative", "frac_negative", "gini_coefficient",
                                         "avg_disapprovals_per_voter", "avg_elected_disapprovals_per_voter"]},
                    "hamming_distance": hamming_trad.loc[r1, r2],
                })


        #Cross Hamming
        for pair_label, dist in cross_hamming.items():
            rows.append({
                "dataset": dataset,
                "method": "Cross-Hamming",
                "rule": pair_label,
                "committee_size": None,
                **{k: None for k in ["elected_mean_net_score", "elected_min_net_score", "elected_max_net_score",
                                     "non_elected_mean_net_score", "best_non_elected_score",
                                     "best_non_elected_candidate",
                                     "mean_utility", "median_utility", "n_zero_or_negative",
                                     "frac_zero_or_negative",
                                     "n_negative", "frac_negative", "gini_coefficient",
                                     "avg_disapprovals_per_voter", "avg_elected_disapprovals_per_voter"]},
                "hamming_distance": dist,
            })

    df_out = pd.DataFrame(rows)
    out_path = os.path.join(output_dir, "metrics_real_world.csv")
    df_out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nReal-world metrics saved to {out_path}.")

    return df_out

#Synthetic Metrics

def compute_synthetic_metrics():
    rows = []

    metric_keys = ["elected_mean_net_score", "elected_min_net_score", "elected_max_net_score",
                   "non_elected_mean_net_score", "best_non_elected_score", "best_non_elected_candidate",
                   "mean_utility", "median_utility", "n_zero_or_negative", "frac_zero_or_negative",
                   "n_negative", "frac_negative", "gini_coefficient",
                   "avg_disapprovals_per_voter", "avg_elected_disapprovals_per_voter"]

    for p_val in p_disapprove_values:
        results_folder = os.path.join(synthetic_results, f"pd_{p_val}")
        data_folder = os.path.join(synthetic_data_dir, f"pd_{p_val}")

        if not os.path.exists(results_folder):
            print(f"Skipping, results folder not found: {results_folder}")
            continue

        datasets = [d for d in os.listdir(results_folder) if os.path.isdir(os.path.join(results_folder, d))]

        for dataset in sorted(datasets):
            result_dir = os.path.join(results_folder, dataset)
            data_dir = os.path.join(data_folder, dataset)

            results_csv = os.path.join(result_dir, "winning_committees.csv")
            votes_csv = os.path.join(data_dir, "synthetic_votes.csv")  # Fixed: data_dir not result_dir

            if not os.path.exists(results_csv):
                print(f"  Skipping {dataset}: missing winning_committees.csv")
                continue

            print(f"\nProcessing synthetic pd={p_val}: {dataset}")

            results_df = pd.read_csv(results_csv, encoding="utf-8")
            all_committees = get_committees_from_results(results_df)


            # Load vote matrix
            if os.path.exists(votes_csv):
                vote_matrix, candidate_cols = load_vote_matrix(votes_csv)
                net_scores = compute_net_scores(vote_matrix, len(candidate_cols))
            else:
                print(f"  Warning: No votes csv found for {dataset}.")
                vote_matrix = None
                net_scores = None

            trad_committees = {r: c for r, c in all_committees.items() if
                               r in ("PAV", "SeqPhragmen", "MES")}
            tax_committees = {r: c for r, c in all_committees.items() if r in ("TaxPhragmen", "TaxMES")}
            av_committees = {r: c for r, c in all_committees.items() if r == "AV"}
            trad_and_av = {**trad_committees, **av_committees}

            # Hamming distances
            hamming_trad = compute_hamming_matrix(trad_and_av)
            hamming_tax = compute_hamming_matrix(tax_committees)
            cross_hamming = compute_cross_hamming(trad_and_av, tax_committees)

            # Extract metadata from results
            meta = {}
            for col in ["Model", "p", "phi", "num_voters", "num_candidates"]:
                if col in results_df.columns:
                    meta[col.lower()] = results_df[col].iloc[0]

            #Per rule metrics
            for rule, committee in all_committees.items():
                method = "Tax" if rule in tax_committees else ("AV" if rule in av_committees else "Traditional")
                row = {
                    "dataset": dataset,
                    "p_disapprove": p_val,
                    "method": method,
                    "rule": rule,  # Fixed: was "rue"
                    "committee_size": len(committee),
                }
                row.update(meta)

                if net_scores is not None:
                    row.update(net_score_summary(net_scores, committee))
                    utilities = compute_voter_utilities(vote_matrix, committee, net_scores)
                    row.update(voter_utility_metrics(utilities))
                    row["avg_disapprovals_per_voter"] = avg_disapproval_per_voter(vote_matrix)
                    row["avg_elected_disapprovals_per_voter"] = disapproval_avoidance(vote_matrix, committee)
                else:
                    for key in metric_keys:
                        row[key] = None

                rows.append(row)

            #Hamming_cross
            for r1, r2 in [("PAV", "SeqPhragmen"), ("PAV", "MES"), ("SeqPhragmen", "MES"), ("AV", "PAV"), ("AV", "SeqPhragmen"), ("AV", "MES")]:
                if r1 in trad_and_av and r2 in trad_and_av:
                    hamming_row = {
                        "dataset": dataset,
                        "p_disapprove": p_val,
                        "method": "Hamming_Traditional",
                        "rule": f"{r1}_vs_{r2}",
                        "committee_size": None,
                        "hamming_distance": hamming_trad.loc[r1, r2],
                    }
                    hamming_row.update(meta)
                    for key in metric_keys:
                        hamming_row[key] = None
                    rows.append(hamming_row)

            for pair_label, dist in cross_hamming.items():
                cross_row = {
                    "dataset": dataset,
                    "p_disapprove": p_val,
                    "method": "Cross_Hamming",
                    "rule": pair_label,
                    "committee_size": None,
                    "hamming_distance": dist,
                }
                cross_row.update(meta)
                for key in metric_keys:
                    cross_row[key] = None
                rows.append(cross_row)

    df_out = pd.DataFrame(rows)
    out_path = os.path.join(output_dir, "metrics_synthetic.csv")
    df_out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nSynthetic metrics saved to {out_path}.")
    return df_out


#Main
if __name__ == "__main__":
    print("=" * 50)
    print("Computing real-world metrics...")
    print("=" * 50)
    df_rw = compute_realworld_metrics()

    print("\n" + "=" * 50)
    print("Computing synthetic metrics...")
    print("=" * 50)
    df_syn = compute_synthetic_metrics()

    print("\nDone.")
    print(f"Real-world rows: {len(df_rw)}")
    print(f"Synthetic rows:  {len(df_syn)}")













