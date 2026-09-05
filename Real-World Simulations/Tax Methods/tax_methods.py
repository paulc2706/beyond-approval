import sys
import os
import pandas as pd
from trivoting.election import Alternative, TrichotomousBallot, TrichotomousProfile
from trivoting.rules import tax_method_of_equal_shares, tax_sequential_phragmen

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Traditional Methods"))

def compute_candidate_stats(df_votes):
    candidate_cols = [col for col in df_votes.columns if col.isdigit()]
    stats = {}

    #Get candidate approvals & disapprovals
    for c_id in candidate_cols:
        c = int(c_id)
        stats[c] = {
            "approvals": int((df_votes[c_id] == 1).sum()),
            "disapprovals": int((df_votes[c_id] == -1).sum())
        }

    return stats

def build_trichotomous_profile(df_votes):
    #Builds the trichotomous profile with their approval and disapproval votes

    candidates_col = [col for col in df_votes.columns if col.isdigit()]

    #Create alternative objects
    alternatives = {int(c_id): Alternative(c_id) for c_id in candidates_col}

    #Build the ballot
    ballots = []
    for _, row in df_votes.iterrows():
        approved = [alternatives[int(c_id)] for c_id in candidates_col if row[c_id] == 1]
        disapproved = [alternatives[int(c_id)] for c_id in candidates_col if row[c_id] == -1]
        ballots.append(TrichotomousBallot(approved=approved, disapproved=disapproved))

    tri_profile = TrichotomousProfile(ballots, alternatives=set(alternatives.values()))

    return tri_profile, alternatives

def run_tax_methods(tri_profile, committee_size):
    #Runs Tax-MES and Tax-Phragmen on the Tri-profile
    #Tax increases the cost of disapproved candidates, filtering out those with more opponents than supporters entirely.

    results = {}

    print("Computing Tax-Phragmén...")
    results["TaxPhragmen"] = tax_sequential_phragmen(tri_profile, committee_size)

    print("Computing Tax-MES... ")
    results["TaxMES"] = tax_method_of_equal_shares(tri_profile, committee_size)

    return results

def save_tax_results(results, output_txt_path, output_csv_path):
    #Saves Tax-MES and Tax-Phragmen results to txt and csv files.
    with open(output_txt_path, "w") as f:
        f.write("==================================================\n")
        f.write("        WINNING COMMITTEES - TAX METHODS          \n")
        f.write("==================================================\n\n")

        for rule, selection in results.items():
            committee = sorted([int(str(a)) for a in selection.selected])
            f.write(f"--- {rule} ---\n")
            f.write(f"  Committee size: {len(committee)}\n")
            cand_str = ", ".join(map(str, committee))
            f.write(f"  Selected candidates: [{cand_str}]\n\n")

    print(f"Tax results saved to: {output_txt_path}")

    rows = []
    for rule, selection in results.items():
        committee = sorted([int(str(a)) for a in selection.selected])
        rows.append({
            "Rule": rule,
            "Committee_Size": len(committee),
            "Selected_Candidates": str(committee)
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)
    print(f"Tax results CSV saved to: {output_csv_path}")

