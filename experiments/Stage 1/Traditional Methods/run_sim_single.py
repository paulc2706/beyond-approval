from traditional_methods import *

input_data = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master\american-assembly.bowling-green\participants-votes.csv"
output_data = "./results_traditional.csv"
output_img = "committee_heatmap.png"

output_committees_txt = "winning_committees.txt"
output_committees_csv = "winning_committees.csv"

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