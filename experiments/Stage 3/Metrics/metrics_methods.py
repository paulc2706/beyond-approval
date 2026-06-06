import numpy as np
import pandas as pd
from itertools import combinations

#Metric functions for analyzing trichotomous votes


#Parsingn helper function

def parse_candidates_lists(s):
    #Parsing of a string into a python list of integers
    s = str(s).strip()
    if s in ("", "nan", "[]"):
        return []
    s = s.strip("[]")

    return [int(x.strip()) for x in s.split(",") if x.strip() != ""]

#Hamming Distance

def hamming_distance(committee_a, committee_b):
    #Symmetric difference between two committees
    return len(set(committee_a).symmetric_difference(set(committee_b)))

def compute_hamming_matrix(committees_dict):
    #Compute pairwise Hamming Distances between rules
    #Returns symmetric matrix of hamming distances
    rules = list(committees_dict.keys())
    matrix = pd.DataFrame(index=rules, columns=rules, dtype=float)
    for r1, r2 in [(a, b) for a in rules for b in rules]:
        matrix.loc[r1, r2] = hamming_distance( committees_dict[r1], committees_dict[r2])

    return matrix


def compute_cross_hamming(traditional_dict, tax_dict):
    #Hamming distances between natural counterpart methods
    pairs = [
        ("PAV", "TaxMES"),
        ("SeqPhragmen", "TaxPhragmen"),
        ("MES", "TaxMES"),
    ]
    results = {}
    for trad, tax in pairs:
        if trad in traditional_dict: and tax in tax_dict:
        results[f"{trad}_vs_{tax}"] = hamming_distance(traditional_dict[trad], tax_dict[tax])

    return results

#Net Score

def compute_net_scores(vote_matrix, num_candidates):
    #Computes the net score (approvals-disapprovals) for every candidate
    candidates_cols = [c for c in vote_matrix.columns if c != "voter_id"]
    net = vote_matrix[candidates_cols].apply(lambda col: (col == 1).sum() - (col == -1).sum())

    return net

def net_score_summary(net_scores, elected_committee):
    #Splits the net scores into elected and non-elected and returns summary
    elected_set = set(elected_committee)
    all_candidates = net_scores.index.tolist()
    non_elected = [c for c in all_candidates if c not in elected_set]

    elected_scores = net_scores[list(elected_set)] if elected_set else pd.Series(dtype=float)
    non_elected_scores = net_scores[non_elected] if non_elected else pd.Series(dtype=float)

    result = {
        "elected_mean_net_score": round(elected_scores.mean(), 4) if len(elected_scores) > 0 else None,
        "elected_min_net_score": round(elected_scores.min(), 4) if len(elected_scores) > 0 else None,
        "elected_max_net_score": round(elected_scores.max(), 4) if len(elected_scores) > 0 else None,
    }

    if len(non_elected_scores) > 0:
        best_idx = non_elected_scores.idxmax()
        result["non_elected_mean_net_score"] = round(non_elected_scores.mean(), 4)
        result["best_non_elected_score"] = round(non_elected_scores[best_idx], 4)
        result["best_non_elected_candidate"] = int(best_idx)
    else:
        result["non_elected_mean_net_score"] = None
        result["best_non_elected_score"] = None
        result["best_non_elected_candidate"] = None

    return result

#Voter utility

def compute_voter_utilities(vote_matrix, elected_committee, net_scores):
    pass

#Disapproval Metrics

def avg_disapproval_per_voter(vote_matrix):
    #Average number of candidates disapproved per voter
    candidates_cols = [c for c in vote_matrix.columns if c != "voter_id"]
    disapprovals_per_voter = (vote_matrix[candidates_cols] == -1).sum(axis=1)

    return round(float(disapprovals_per_voter.mean()), 4)

def disapproval_avoidance(vote_matrix, elected_committee):
    #Counts for each voter how many elected candidates they disapproved of
    elected_cols = [c for c in elected_committee if c in vote_matrix.columns]
    if not elected_cols:
        return 0.0
    elected_disapprovals = (vote_matrix[elected_cols] == -1).sum(axis=1)

    return round(float(elected_disapprovals.mean()), 4)


#Committee Size

def committee_size_metrics(committees_dict):
    #Returns committee size per rule
    return {rule: len(committee) for rule, committee in committees_dict.items()}