import os
import pandas as pd
from traditional_methods import *

#Folder Configuration
data_folder = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master"
output_folder = "./Results/"

#Committee size
committee_size = 10

#Batch Processing
def run_batch_processing():
    #Identify all relevant folders
    dataset_folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]

    print(f"Found {len(dataset_folders)} datasets. Starting batch processing.")

    for dataset_folder in dataset_folders:
        print(f"Processing Dataset {dataset_folder}")

        #Filepath Definition
        input_file = os.path.join(data_folder, dataset_folder, "participants-votes.csv")

        #Skip if the relevant file is missing
        if not os.path.exists(input_file):
            print(f"Skipping {dataset_folder}: relevant File not found")
            continue

        #Output setup
        result_path = os.path.join(output_folder, dataset_folder)
        os.makedirs(result_path, exist_ok=True)

        #Processing Pipeline
        try:
            profile, df_raw = load_profiles(input_file)
            results = run_methods(profile, committee_size)

            #Frequency Matrix
            matrix = create_frequency_matrix(results, profile.num_cand)

            #Output paths
            csv_path = os.path.join(result_path, "frequency_matrix.csv")
            vis_path = os.path.join(result_path, "heatmap.png")
            txt.path = os.path.join(result_path, "winning_committees.txt")
            committiees_csv = os.path.join(result_path, "winning_committees_list.csv")

            #Visualize and Save
            visualize_and_save(matrix, csv_path, vis_path)
            save_winning_committees(results, txt_path, committiees_csv)

            #Progress Message
            print_winning_committees(results)
            print(f"Successfully processed {dataset_folder}")

        except  Exception as e:
            print(f"Error processing {dataset_folder}: {e}")


if __name__ == "__main__":
    run_batch_processing()