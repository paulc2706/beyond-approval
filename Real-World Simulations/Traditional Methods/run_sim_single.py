from traditional_methods import *
from pathlib import Path

root = Path(__file__).resolve().parents[2]
input_data = str(root / "Data" / "Real-World" / "openData-master" / "american-assembly.bowling-green" / "participants-votes.csv")

results_dir = root / "Results" / "Results Real-World" / "american-assembly.bowling-green"
results_dir.mkdir(parents=True, exist_ok=True)
output_data = str(results_dir / "results_traditional.csv")
output_img = str(results_dir / "committee_heatmap.png")

output_committees_txt = str(results_dir / "winning_committees.txt")
output_committees_csv = str(results_dir / "winning_committees.csv")

#Load
profile, df_raw, reverse_map = load_profiles(input_data)

#Compute
results_mapped = run_methods(profile, 10)

#Map back
results = {}
for rule, committees in results_mapped.items():
    results[rule] = [[reverse_map[c] for c in comm] for comm in committees]


#Print
print_winning_committees(results)

#Matrix & Save
matrix = create_frequency_matrix(results, sorted(reverse_map.values()))
visualize_and_save(matrix, output_data, output_img)

#save_winning_committees(results, output_committees_txt, output_committees_csv)