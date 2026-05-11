import pandas as pd
from abcvoting import abcrules
from abcvoting.preferences import Profile

file_path = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master\15-per-hour-seattle\participants-votes.csv"

#Load the votes
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

profile = Profile(num_cand=54)
profile.add_voters(approval_sets)
#profile.add_voters(disapproval_sets)

print(f"Loaded profile with {len(profile)} voters and {profile.num_cand} candidates.)")

#Run the methods
committee_size = 5

#PAV
committees_pav = abcrules.compute_pav(profile, committeesize= committee_size)
print("PAV Elected Committee(s):", committees_pav)

#Sequential Phragmén
committees_phragmen = abcrules.compute_seqphragmen(profile, committeesize= committee_size)
print("Seq-Phragén Elected Committee(s):", committees_phragmen)

#MES
committees_mes = abcrules.compute_rule_x(profile, committeesize= committee_size)
print("Mes Elected Committee(s):", committees_mes)
