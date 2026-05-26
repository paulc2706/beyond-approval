import os
import numpy as np
import pandas as pd
import functools
from abcvoting.preferences import Profile
from trivoting.election import Alternative, TrichotomousBallot, TrichotomousProfile
from prefsampling.approval import impartial, resampling, euclidean_threshold
from prefsampling.point import ball_uniform

def generate_trichotomous_votes(approval_sets, num_candidates, p_disapprove, seed=None):
    #Extends the approval sets from prefsampling with disapprovals, with p_disapprove or else abstain for each non-approved candidate
    rng = np.random.default_rng(seed)
    num_voters = len(approval_sets)
    #Initializes a matrix, voters X candidates with 0 as a default
    votes = np.zeros((num_voters, num_candidates), dtype=int)

    for i, approved, in enumerate(approval_sets):
        for c in range(num_candidates):
            if c in approved:
                votes[i, c] = 1
            else:
                votes[i, c] = -1 if rng.random() < p_disapprove else 0 #If not approved, random decision between active disapproval (-1) or abstention

    return votes

def build_profiles(votes, num_candidates):
    #Builds a profile for the traditional methods and a Trichotomous Profile for the Tax Methods
    #1. Traditional Methods
    #Extracting the approval sets as disapprovals are not relevant
    approval_sets = [
        [c for c in range(num_candidates) if votes[i, c] == 1]
        for i in range(len(votes))
    ]
    profile = Profile(num_cand=num_candidates)
    profile.add_voters(approval_sets)

    #2. Trichotomous Profile for Tax Methods
    alternatives = {c: Alternative(str(c)) for c in range(num_candidates)}
    ballots = []
    for i in range(len(votes)):
        approved = [alternatives[c] for c in range(num_candidates) if votes[i, c] == 1]
        disapproved = [alternatives[c] for c in range(num_candidates) if votes[i, c] == -1]
        ballots.append(TrichotomousBallot(approved=approved, disapproved=disapproved))

    tri_profile = TrichotomousProfile(ballots, alternatives=set(alternatives.values()))

    return profile, tri_profile

def sample_resampling(num_voters, num_candidates, p, phi, p_disapprove, seed=None):
    approval_sets = resampling(num_voters, num_candidates, phi=phi, rel_size_central_vote=p, seed=seed)
    votes = generate_trichotomous_votes(approval_sets, num_candidates, p_disapprove, seed=seed)
    profile, tri_profile = build_profiles(votes, num_candidates)
    return profile, tri_profile, votes

def sample_impartial(num_voters, num_candidates, p, p_disapprove, seed=None):
    approval_sets = impartial(num_voters, num_candidates, p=p, seed=seed)
    votes = generate_trichotomous_votes(approval_sets, num_candidates, p_disapprove, seed=seed)
    profile, tri_profile = build_profiles(votes, num_candidates)
    return profile, tri_profile, votes

def sample_euclidean_threshold(num_voters, num_candidates, radius, p_disapprove, seed=None):
    #Defines 2D uniform ball distributions for placing voters and candidates spatially
    voters_pos = functools.partial(ball_uniform, num_dimensions = 2)
    candidates_pos = functools.partial(ball_uniform, num_dimensions = 2)
    approval_sets = euclidean_threshold(num_voters, num_candidates, threshold=radius, num_dimensions=2, voters_positions=voters_pos, candidates_positions=candidates_pos, seed=seed)
    votes = generate_trichotomous_votes(approval_sets, num_candidates, p_disapprove, seed=seed)
    profile, tri_profile = build_profiles(votes, num_candidates)
    return profile, tri_profile, votes

def save_synthetic_dataset(votes, params, output_path):
    #Saves the raw votes as a csv in the same format as the real data --> Columns = candidate IDs, values 1, -1, 0
    os.makedirs(output_path, exist_ok=True)
    num_candidates = votes.shape[1]
    df = pd.DataFrame(votes, columns=[str(c) for c in range(num_candidates)])

    #Voter index column for reference
    df.insert(0, "voter_id", range(len(df)))

    #Save the parameters as a separate file
    dataset_csv = os.path.join(output_path, "synthetic_votes.csv")
    metadata_path = os.path.join(output_path, "metadata.txt")

    df.to_csv(dataset_csv, index=False)

    with open(metadata_path, "w") as f:
        f.write("Synthetic Dataset Parameters\n")
        f.write("=" * 40 + "\n")
        for k, v in params.items():
            f.write(f"{k}: {v}\n")

    print(f"Dataset saved to {dataset_csv}")

def load_synthetic_dataset(dataset_path):
    csv_path = os.path.join(dataset_path, "synthetic_votes.csv")
    df = pd.read_csv(csv_path)

    #Drop the id column
    candidate_cols = [col for col in df.columns if col.isdigit()]
    num_candidates = len(candidate_cols)
    votes = df[candidate_cols].values.astype(int)

    profile, tri_profile = build_profiles(votes, num_candidates)
    return profile, tri_profile


def save_synthetic_results(results_traditional, results_tax, params, output_path):
    #Saves the results of the traditional methods and tax methods on the synthetic dataset
    os.makedirs(output_path, exist_ok=True)

    txt_path = os.path.join(output_path, "winning_committees.txt")
    csv_path = os.path.join(output_path, "winning_committees.csv")

    #Save as a .txt

    with open(txt_path, "w") as f:
        f.write("==================================================\n")
        f.write("     WINNING COMMITTEES - SYNTHETIC DATA          \n")
        f.write("==================================================\n\n")
        f.write(f"Parameters: {params}\n\n")

        f.write("--- Traditional Methods ---\n")
        for rule, committees in results_traditional.items():
            f.write(f"\n{rule}:\n")
            for idx, committee in enumerate(committees):
                cand_str = ", ".join(map(str, sorted(committee)))
                f.write(f"  Committee {idx + 1}: [{cand_str}]\n")

        f.write("\n--- Tax Methods ---\n")
        for rule, selection in results_tax.items():
            committee = sorted([int(str(a)) for a in selection.selected])
            cand_str = ", ".join(map(str, committee))
            f.write(f"\n{rule}: [{cand_str}]\n")

    #Save as a csv
    rows = []
    for rule, committees in results_traditional.items():
        for idx, committee in enumerate(committees):
            rows.append({
                "Method": "Traditional",
                "Rule": rule,
                "Committee_Index": idx + 1,
                "Committee_Size": len(committee),
                "Selected_Candidates": str(sorted(committee)),
                **params
            })
    for rule, selection in results_tax.items():
        committee = sorted([int(str(a)) for a in selection.selected])
        rows.append({
            "Method": "Tax",
            "Rule": rule,
            "Committee_Index": 1,
            "Committee_Size": len(committee),
            "Selected_Candidates": str(committee),
            **params
        })

    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"Results saved to: {output_path}")
