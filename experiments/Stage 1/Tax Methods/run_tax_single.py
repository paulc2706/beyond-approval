if __name__ == "__main__":
    test_file = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master\american-assembly.bowling-green\participants-votes.csv"
    committee_size = 10

    profile, df_raw, reverse_map = load_profiles(test_file)

    #Test Stats
    stats = compute_candidate_stats(df_raw)

    print(f"Total Candidates: {len(stats)}")
    print(f"\nFirst 5 candidates:")
    for c_id, s in list(stats.items())[:5]:
        print(f"  Candidate {c_id}: approvals={s["approvals"]}, disapprovals={s["disapprovals"]}")

    candidates_with_disapprovals = sum(1 for s in stats.values() if s["disapprovals"] > 0)
    print(f"\nCandidates with at least one disapproval: {candidates_with_disapprovals}/{len(stats)}")

    #Build Tri-profiles
    tri_profile, alternatives = build_trichotomous_profile(df_raw)
    print(f"\nTrichotomous profile built: {len(tri_profile)} voters, {len(alternatives)} alternatives")

    #Run tax-methods
    results = run_tax_methods(tri_profile, committee_size)

    #Print results
    for rule, selection in results.items():
        elected = sorted([str(a) for a in selection.selected])
        print(f"\n{rule}: {elected}")

    save_tax_results(results, "./test_tax_results.txt", "./test_tax_results.csv")
