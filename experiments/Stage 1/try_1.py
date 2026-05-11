import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from abcvoting import abcrules
from abcvoting.preferences import Profile
from pyparsing import results


#Load the votes
def load_profiles(file_path):
    df_votes = pd.read_csv(file_path)

    candidate_cols = [col for col in df_votes.columns if col.isdigit()]

    #Create Approval and Disapproval profiles
    approval_sets = []
    disapproval_sets = []

    for index, row in df_votes.iterrows():
        approved_candidates = []
        disapproved_candidates = []

        for  c_id in candidate_cols:
            vote_value = row[c_id]

            if vote_value == 1:
                approved_candidates.append(int(c_id))
            elif vote_value == -1:
                disapproved_candidates.append(int(c_id))

        approval_sets.append(approved_candidates)
        disapproval_sets.append(disapproved_candidates)

    profile = Profile(num_cand=len(candidate_cols))
    profile.add_voters(approval_sets)
    #profile.add_voters(disapproval_sets)

    print(f"Loaded profile with {len(profile)} voters and {profile.num_cand} candidates.)")

    return profile, df_votes



#Run the methods
def run_methods(profile, committee_size):
    results = {}

    #PAV
    print(f"Computing PAV...")
    committees_pav = abcrules.compute_pav(profile, committeesize= committee_size)
    results["PAV"] = [list(c) for c in  committees_pav]

    #Sequential Phragmén
    print(f"Computing Seq-Phragmén...")
    committees_phragmen = abcrules.compute_seqphragmen(profile, committeesize= committee_size)
    results["SeqPhragmen"] = [list(c) for c in  committees_phragmen]

    #MES
    print(f"Computing MES...")
    committees_mes = abcrules.compute_rule_x(profile, committeesize= committee_size)
    results["MES"] = [list(c) for c in committees_mes]

    return results

def create_frequency_matrix(results, num_candidates):
    matrix = pd.DataFrame(0.0, index=range(num_candidates), columns=results.keys())

    for rule, committees in results.items():
        num_ties  = len(committees)
        for committee in committees:
            for cand in committee:
                matrix.at[cand, rule] += (1.0 / num_ties)

    return matrix

def calculate_hamming_distance(results):
    rules_names = list(results.keys())
    dist_matrix = pd.DataFrame(index=rules_names, columns=rules_names)

    for r1 in rules_names:
        for r2 in rules_names:
            distances = []
            for comm1 in results[r1]:
                set1 = set(comm1)
                for comm2 in results[r2]:
                    set2 = set(comm2)
                    distance = len(set1.symmetric_difference(set2))
                    distances.append(distance)

            dist_matrix.loc[r1, r2] = np.mean(distances)

    return dist_matrix

def visualize_and_save(matrix, output_csv_path, output_img_path):
    matrix.to_csv(output_csv_path)

    plt.figure(figsize=(10,12))
    sns.heatmap(matrix, cmap="YlGnBu", annot=False, cbar_kws={"label": "Selection Probability"})
    plt.title("Committee Comparison (Including Tied Committees)")
    plt.xlabel("Voting Rule")
    plt.ylabel("Cadidate ID")
    plt.tight_layout()
    plt.savefig(output_img_path)
    plt.show()


def save_winning_committees(results, output_txt_path, output_csv_path):
    with open(output_txt_path, "w") as f:
        f.write("==================================================\n")
        f.write("           WINNING COMMITTEES BY METHOD           \n")
        f.write("==================================================\n\n")

        for rule, committees in results.items():
            f.write(f"--- {rule} ({len(committees)} winning committee(s) found) ---\n")
            for idx, committee in enumerate(committees):
                # Format candidate IDs nicely, e.g., "1, 4, 15, 23"
                cand_str = ", ".join(map(str, sorted(committee)))
                f.write(f"  Committee {idx + 1}: [{cand_str}]\n")
            f.write("\n")

    print(f"Human-readable committees saved to: {output_txt_path}")

    rows = []
    for rule, committees in results.items():
        for idx, committee in enumerate(committees):
            rows.append({
                "Rule": rule,
                "Committee_Index": idx + 1,
                "Committee_Size": len(committee),
                "Selected_Candidates": str(sorted(committee))
            })

    df_committees = pd.DataFrame(rows)
    df_committees.to_csv(output_csv_path, index=False)
    print(f"Structured committees CSV saved to: {output_csv_path}")


def print_winning_committees(results):
    print("\n" + "=" * 50)
    print("           WINNING COMMITTEES BY METHOD           ")
    print("=" * 50)

    for rule, committees in results.items():
        print(f"\n--- {rule} ({len(committees)} winning committee(s) found) ---")
        for idx, committee in enumerate(committees):
            cand_str = ", ".join(map(str, sorted(committee)))
            print(f"  Committee {idx + 1}: [{cand_str}]")

    print("\n" + "=" * 50 + "\n")