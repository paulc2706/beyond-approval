from try_1 import *

input_data = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master\15-per-hour-seattle\participants-votes.csv"
output_data = "./results_traditional.csv"
output_img = "committee_heatmap.png"

output_committees_txt = "winning_committees.txt"
output_committees_csv = "winning_committees.csv"

#Load
profile, df_raw = load_profiles(input_data)

#Compute
results = run_methods(profile, 10)

#Print
print_winning_committees(results)

#Matrix & Save
matrix = create_frequency_matrix(results, profile.num_cand)
visualize_and_save(matrix, output_data, output_img)

#save_winning_committees(results, output_committees_txt, output_committees_csv)