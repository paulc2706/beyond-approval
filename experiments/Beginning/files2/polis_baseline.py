"""
polis_baseline.py
=================
Loads a pol.is conversation export and runs PAV, sequential Phragmén,
and MES (with seqPhragmén completion) over the real-world approval data.

Vote encoding (pol.is):
    1   = agree   → approved
   -1   = disagree → disapproved  (stored for later Tax-MES; ignored by baseline rules)
    0   = pass    → abstain (not in approval or disapproval set)
  blank = never saw the comment → abstain (same treatment as pass)

Only comments with moderated == 1 (accepted) are included as candidates.

Usage
-----
    python polis_baseline.py --data-dir /path/to/polis/export/
    python polis_baseline.py --data-dir . --k 6 10 15
    python polis_baseline.py --data-dir . --k 6 10 15 --min-votes 1
"""

import argparse
import csv
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

from abcvoting import abcrules
from abcvoting.preferences import Profile, Voter


# ── Data loading ──────────────────────────────────────────────────────────────

def load_polis_export(data_dir: Path, min_votes: int = 0):
    """
    Load a pol.is export directory and return:
        accepted_ids  : list[str]  — comment IDs of accepted comments, sorted by int
        cand_map      : dict[str, int] — comment ID → 0-based candidate index
        idx_to_cid    : dict[int, str] — reverse map
        trichotomous  : list[tuple[frozenset, frozenset]]
                        one entry per voter: (approved_indices, disapproved_indices)
        comment_meta  : dict[str, dict] — comment metadata keyed by comment-id
        summary       : dict[str, str]  — contents of summary.csv
        n_empty       : int — voters with no signal on accepted comments
        n_below_min   : int — voters dropped for having fewer than min_votes votes
    """
    comments_path  = data_dir / "comments.csv"
    pv_path        = data_dir / "participants-votes.csv"
    summary_path   = data_dir / "summary.csv"

    # ── Comments ──
    with open(comments_path, encoding="utf-8") as f:
        all_comments = list(csv.DictReader(f))

    comment_meta = {r["comment-id"]: r for r in all_comments}
    accepted_ids = sorted(
        [r["comment-id"] for r in all_comments if r["moderated"] == "1"],
        key=int,
    )
    assert len(accepted_ids) > 0, "No accepted comments found."

    cand_map   = {cid: idx for idx, cid in enumerate(accepted_ids)}
    idx_to_cid = {idx: cid for cid, idx in cand_map.items()}
    num_cand   = len(accepted_ids)

    # ── Summary ──
    summary = {}
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) == 2:
                    summary[row[0]] = row[1]

    # ── Participants / votes ──
    with open(pv_path, encoding="utf-8") as f:
        prows = list(csv.DictReader(f))

    trichotomous = []
    n_empty      = 0
    n_below_min  = 0

    for r in prows:
        approved    = frozenset(
            cand_map[c] for c in accepted_ids if r.get(c) == "1"
        )
        disapproved = frozenset(
            cand_map[c] for c in accepted_ids if r.get(c) == "-1"
        )
        total_votes = len(approved) + len(disapproved)

        if total_votes < min_votes:
            n_below_min += 1
            continue

        if not approved and not disapproved:
            n_empty += 1

        trichotomous.append((approved, disapproved))

    return (
        accepted_ids, cand_map, idx_to_cid,
        trichotomous, comment_meta, summary,
        n_empty, n_below_min,
    )


def build_approval_profile(trichotomous: list, num_cand: int) -> Profile:
    """Build an abcvoting Profile using only the approval (agree) part."""
    profile = Profile(num_cand=num_cand)
    for approved, _ in trichotomous:
        profile.add_voter(Voter(approved=sorted(approved)))
    return profile


# ── Metrics ───────────────────────────────────────────────────────────────────

def hamming(A: set, B: set) -> int:
    return len(A.symmetric_difference(B))


def approval_score(winners: set, trichotomous: list) -> float:
    """Sum of |W ∩ Aᵢ| across all voters (pure approval score)."""
    return sum(len(winners & a) for a, _ in trichotomous)


def disapproval_count(winners: set, trichotomous: list) -> int:
    """Total number of (voter, candidate) pairs where candidate is in W and voter disapproves it."""
    return sum(len(winners & d) for _, d in trichotomous)


def avg_ballot_coverage(winners: set, trichotomous: list) -> float:
    """Fraction of voters who have at least one approved winner."""
    if not trichotomous:
        return 0.0
    covered = sum(1 for a, _ in trichotomous if winners & a)
    return covered / len(trichotomous)


# ── Rule runner ───────────────────────────────────────────────────────────────

@dataclass
class RunResult:
    k:                   int
    n_voters:            int
    n_candidates:        int
    n_empty_ballots:     int
    n_below_min_dropped: int

    pav_winners:         list = field(default_factory=list)
    phrag_winners:       list = field(default_factory=list)
    mes_winners:         list = field(default_factory=list)

    # Comment IDs of winners (human-readable)
    pav_comment_ids:     list = field(default_factory=list)
    phrag_comment_ids:   list = field(default_factory=list)
    mes_comment_ids:     list = field(default_factory=list)

    hamming_pav_phrag:   int   = 0
    hamming_pav_mes:     int   = 0
    hamming_phrag_mes:   int   = 0

    pav_approval_score:   float = 0.0
    phrag_approval_score: float = 0.0
    mes_approval_score:   float = 0.0

    # How many disapproved candidates ended up elected
    pav_disapproval_count:   int = 0
    phrag_disapproval_count: int = 0
    mes_disapproval_count:   int = 0

    # Fraction of voters with ≥1 approved winner
    pav_coverage:    float = 0.0
    phrag_coverage:  float = 0.0
    mes_coverage:    float = 0.0

    runtime_pav:    float = 0.0
    runtime_phrag:  float = 0.0
    runtime_mes:    float = 0.0

    error: str = ""


def run_one_k(
    k: int,
    trichotomous: list,
    accepted_ids: list,
    idx_to_cid: dict,
    n_empty: int,
    n_below_min: int,
) -> RunResult:
    num_cand = len(accepted_ids)
    result = RunResult(
        k=k,
        n_voters=len(trichotomous),
        n_candidates=num_cand,
        n_empty_ballots=n_empty,
        n_below_min_dropped=n_below_min,
    )

    try:
        profile = build_approval_profile(trichotomous, num_cand)

        t0 = time.perf_counter()
        pav_w = set(abcrules.compute_pav(profile, k, resolute=True)[0])
        result.runtime_pav = round(time.perf_counter() - t0, 4)

        t0 = time.perf_counter()
        phrag_w = set(abcrules.compute_seqphragmen(profile, k, resolute=True)[0])
        result.runtime_phrag = round(time.perf_counter() - t0, 4)

        t0 = time.perf_counter()
        mes_w = set(
            abcrules.compute_equal_shares(
                profile, k, resolute=True, completion="seqphragmen"
            )[0]
        )
        result.runtime_mes = round(time.perf_counter() - t0, 4)

        def to_cids(ws):
            return sorted([idx_to_cid[i] for i in ws], key=int)

        result.pav_winners   = sorted(pav_w)
        result.phrag_winners = sorted(phrag_w)
        result.mes_winners   = sorted(mes_w)

        result.pav_comment_ids   = to_cids(pav_w)
        result.phrag_comment_ids = to_cids(phrag_w)
        result.mes_comment_ids   = to_cids(mes_w)

        result.hamming_pav_phrag = hamming(pav_w, phrag_w)
        result.hamming_pav_mes   = hamming(pav_w, mes_w)
        result.hamming_phrag_mes = hamming(phrag_w, mes_w)

        result.pav_approval_score    = approval_score(pav_w, trichotomous)
        result.phrag_approval_score  = approval_score(phrag_w, trichotomous)
        result.mes_approval_score    = approval_score(mes_w, trichotomous)

        result.pav_disapproval_count   = disapproval_count(pav_w, trichotomous)
        result.phrag_disapproval_count = disapproval_count(phrag_w, trichotomous)
        result.mes_disapproval_count   = disapproval_count(mes_w, trichotomous)

        result.pav_coverage   = round(avg_ballot_coverage(pav_w, trichotomous), 4)
        result.phrag_coverage = round(avg_ballot_coverage(phrag_w, trichotomous), 4)
        result.mes_coverage   = round(avg_ballot_coverage(mes_w, trichotomous), 4)

    except Exception as exc:
        result.error = str(exc)

    return result


# ── Output ────────────────────────────────────────────────────────────────────

def print_result(result: RunResult, comment_meta: dict, idx_to_cid: dict):
    print(f"\n{'='*65}")
    print(f"k = {result.k}   |   voters={result.n_voters}   candidates={result.n_candidates}")
    print(f"  Empty ballots (no signal on accepted comments): {result.n_empty_ballots}")
    print(f"  Voters dropped (below min-votes threshold):     {result.n_below_min_dropped}")

    if result.error:
        print(f"  ERROR: {result.error}")
        return

    print(f"\n  {'Rule':<10} {'Winners (comment IDs)':<35} {'Appr.':>6} {'Disapv.':>8} {'Cov.':>6}")
    print(f"  {'-'*65}")

    for rule, winners, cids, appr, disapv, cov in [
        ("PAV",     result.pav_winners,   result.pav_comment_ids,
         result.pav_approval_score,   result.pav_disapproval_count,   result.pav_coverage),
        ("Phragmén", result.phrag_winners, result.phrag_comment_ids,
         result.phrag_approval_score, result.phrag_disapproval_count, result.phrag_coverage),
        ("MES",     result.mes_winners,   result.mes_comment_ids,
         result.mes_approval_score,   result.mes_disapproval_count,   result.mes_coverage),
    ]:
        cid_str = str(cids)
        print(f"  {rule:<10} {cid_str:<35} {appr:>6.0f} {disapv:>8} {cov:>6.1%}")

    print(f"\n  Pairwise Hamming distances:")
    print(f"    PAV  ↔ Phragmén : {result.hamming_pav_phrag}")
    print(f"    PAV  ↔ MES      : {result.hamming_pav_mes}")
    print(f"    Phragmén ↔ MES  : {result.hamming_phrag_mes}")

    # Show winning comments with their text
    all_winner_cids = sorted(
        set(result.pav_comment_ids) | set(result.phrag_comment_ids) | set(result.mes_comment_ids),
        key=int
    )
    print(f"\n  Elected comments (union across rules):")
    for cid in all_winner_cids:
        meta = comment_meta.get(cid, {})
        a, d = meta.get("agrees", "?"), meta.get("disagrees", "?")
        body = meta.get("comment-body", "")[:72]
        in_rules = []
        if cid in result.pav_comment_ids:   in_rules.append("PAV")
        if cid in result.phrag_comment_ids: in_rules.append("Phrag")
        if cid in result.mes_comment_ids:   in_rules.append("MES")
        print(f"    [{cid:>2}] +{a}/-{d}  ({', '.join(in_rules)})")
        print(f"         {body}")


def write_csv(results: list[RunResult], path: Path):
    if not results:
        return
    skip = {"pav_winners", "phrag_winners", "mes_winners"}
    fieldnames = [f for f in asdict(results[0]).keys() if f not in skip]
    # Serialise comment id lists as JSON strings
    list_fields = {"pav_comment_ids", "phrag_comment_ids", "mes_comment_ids"}

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: v for k, v in asdict(r).items() if k not in skip}
            for lf in list_fields:
                row[lf] = json.dumps(row[lf])
            writer.writerow(row)
    print(f"\nResults written → {path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Run PAV / Phragmén / MES on a pol.is conversation export"
    )
    p.add_argument(
        "--data-dir", type=Path, default=Path(r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master\15-per-hour-seattle"),
        help="Directory containing comments.csv, participants-votes.csv, summary.csv"
    )
    p.add_argument(
        "--k", nargs="+", type=int, default=[6, 10, 15],
        help="Committee size(s) to evaluate (default: 6 10 15)"
    )
    p.add_argument(
        "--min-votes", type=int, default=0,
        help="Drop voters who cast fewer than this many votes on accepted comments (default: 0)"
    )
    p.add_argument(
        "--out", type=Path, default=Path("results_polis.csv"),
        help="Output CSV path (default: results_polis.csv)"
    )
    return p.parse_args()


def main():
    args = parse_args()

    print(f"Loading pol.is export from {args.data_dir} ...")
    (
        accepted_ids, cand_map, idx_to_cid,
        trichotomous, comment_meta, summary,
        n_empty, n_below_min,
    ) = load_polis_export(args.data_dir, min_votes=args.min_votes)

    topic = summary.get("topic", "unknown")
    print(f"  Topic   : {topic}")
    print(f"  Voters  : {len(trichotomous) + n_below_min} total, "
          f"{n_below_min} dropped (min-votes={args.min_votes}), "
          f"{len(trichotomous)} used")
    print(f"  Candidates (accepted comments): {len(accepted_ids)}")
    print(f"  Empty ballots (zero signal):    {n_empty}")
    print(f"  k values to test: {args.k}")

    results = []
    for k in args.k:
        if k > len(accepted_ids):
            print(f"  [skip] k={k} > num_candidates={len(accepted_ids)}")
            continue
        result = run_one_k(k, trichotomous, accepted_ids, idx_to_cid, n_empty, n_below_min)
        results.append(result)
        print_result(result, comment_meta, idx_to_cid)

    write_csv(results, args.out)


if __name__ == "__main__":
    main()
