import os
import sys
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Traditional Methods"))

from traditional_methods import load_profiles
from tax_methods import *

data_folder = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\openData-master"
output_folder = "./Results/"
committee_size = 10

def run_batch_processing():
    dataset_folders = [
        f for f in os.listdir(data_folder)
        if os.path.isdir(os.path.join(data_folder, f))
    ]

    print(f"Found {len(dataset_folders)} datasets. Starting batch processing.")

    for dataset_folder in dataset_folders:
        print(f"\n{'=' * 50}")
        print(f"Processing: {dataset_folder}")

        input_file = os.path.join(data_folder, dataset_folder, "participants-votes.csv")

        if not os.path.exists(input_file):
            print(f"Skipping {dataset_folder}: file not found")
            continue

        results_path = os.path.join(output_folder, dataset_folder)
        os.makedirs(results_path, exist_ok=True)

        try:
            #Load Data
            _, df_raw, _ = load_profiles(input_file)

            #Overview Stats
            stats = compute_candidate_stats(df_raw)

            #Build Tri-profile
            tri_profile, alternatives = build_trichotomous_profile(df_raw)

            #Run Tax-methods
            results = run_tax_methods(tri_profile, committee_size)

            #Print committee sizes
            for rule, selection in results.items():
                print(f"  {rule}: {len(selection.selected)} candidates elected")

            #Save Results
            txt_path = os.path.join(results_path, "tax_winning_committees.txt")
            csv_path = os.path.join(results_path, "tax_winning_committees.csv")
            save_tax_results(results, txt_path, csv_path)

            print(f"Successfully processed {dataset_folder}")

        except Exception as e:
            print(f"Error processing {dataset_folder}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_batch_processing()

    