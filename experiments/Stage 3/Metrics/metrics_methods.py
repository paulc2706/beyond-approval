import numpy as np
import pandas as pd
from itertools import combinations

from networkx.algorithms import flow


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
    #Hamming distances between all traditional-tax pairs and within tax pairs
    pairs = [
        ("PAV", "TaxMES"),
        ("PAV", "TaxPhragmen"),
        ("SeqPhragmen", "TaxPhragmen"),
        ("SeqPhragmen", "TaxMES"),
        ("MES", "TaxMES"),
        ("MES", "TaxPhragmen"),
        ("TaxPhragmen", "TaxMES"),  # within-tax
        ("AV", "TaxMES"),
        ("AV", "TaxPhragmen"),
    ]
    results = {}
    for a, b in pairs:
        a_committee = traditional_dict.get(a) or tax_dict.get(a)
        b_committee = traditional_dict.get(b) or tax_dict.get(b)
        if a_committee is not None and b_committee is not None:
            results[f"{a}_vs_{b}"] = hamming_distance(a_committee, b_committee)

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
#"""
def compute_voter_utilities(vote_matrix, elected_committee, net_scores=None):
    #Per Voter Utility: count of elected candidates the voter approved - count of elected candidates the voter disapproved.
    #net_scores kept as an unused parameter for call-site compatibility with run_metrics.py; no longer weights the utility.
    elected_set = [c for c in elected_committee if c in vote_matrix.columns]
    if not elected_set:
        n = len(vote_matrix)
        return pd.Series(np.zeros(n), index=vote_matrix.index)

    votes_on_elected = vote_matrix[elected_set]

    # utility[v] = sum over elected c of: vote[v,c]  (+1 approved, -1 disapproved, 0 indifferent)
    utilities = votes_on_elected.values.sum(axis=1)
    return pd.Series(utilities, index=vote_matrix.index)
#"""

"""
def compute_voter_utilities(vote_matrix, elected_committee, net_scores):
    #Per Voter Utility: sum of net scores of elected candidates the voter approved - sum of net scores of elected candidates the voter disapproved.
    elected_set = [c for c in elected_committee if c in vote_matrix.columns]
    if not elected_set:
        n = len(vote_matrix)
        return pd.Series(np.zeros(n), index=vote_matrix.index)

    votes_on_elected = vote_matrix[elected_set]
    weights = net_scores[elected_set].values

    # utility[v] = sum over elected c of: vote[v,c] * net_score[c]
    utilities = votes_on_elected.values @ weights
    return pd.Series(utilities, index=vote_matrix.index)
"""

def voter_utility_metrics(utilities):
    #Aggreate voter utility statistics
    n = len(utilities)
    result = {
        "mean_utility": round(float(utilities.mean()), 4),
        "median_utility": round(float(utilities.median()), 4),
        "n_zero_or_negative": int((utilities <= 0).sum()),
        "frac_zero_or_negative": round(float((utilities <= 0).mean()), 4),
        "n_negative": int((utilities < 0).sum()),
        "frac_negative": round(float((utilities < 0).mean()), 4),
        "gini_coefficient": round(_gini(utilities.values), 4),
    }

    return result

def _gini(values):
    #Gini coefficient for an array of values
    arr = np.array(values, dtype=float)
    shift = arr.min()
    if shift < 0:
        arr = arr - shift
    if arr.sum() == 0:
        return 0.0
    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n+1)

    return float((2 * (index * arr).sum()) / (n * arr.sum()) - (n + 1) / n)

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