import os
import sys
import traceback
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Stage 1", "Traditional Methods"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Stage 1", "Tax Methods"))
from traditional_methods import run_methods
from tax_methods import run_tax_methods
from synthetic_methods import load_synthetic_dataset, save_synthetic_results

data_folder = r"C:\Users\paulc\Documents\bachelor-thesis\data\raw\Synthetic Data"
output_folder = r"C:\Users\paulc\Documents\bachelor-thesis\experiments\Results_Synthetic"
Committee_Size = 10

def run_all_methods():
    #Dynamically scans the data folder to find all subdirectories
    dataset_folders = [
        f for f in os.listdir(data_folder)
        if os.path.isdir(os.path.join(data_folder, f))
    ]

    print(f"Found {len(dataset_folders)} datasets")

    for dataset_folder in dataset_folders:
        print(f"\n{"=" * 50}")
        print(f"Running methods on: {dataset_folder}")

        #Sets up mirrored folder tracks
        dataset_path = os.path.join(data_folder, dataset_folder)
        output_path = os.path.join(output_folder, dataset_folder)

        try:
            #Reconstructs the required distinct voting profiles
            profile, tri_profile = load_synthetic_dataset(dataset_path)

            print(f"  Running traditional methods...")
            results_traditional = run_methods(profile, Committee_Size)

            print(f"  Running tax methods...")
            results_tax = run_tax_methods(tri_profile, Committee_Size)

            #Parses the metadata file back into a dictionary to link generation params with results
            params = {"dataset": dataset_folder,}
            metadata_path = os.path.join(dataset_path, "metadata.txt")
            if os.path.exists(metadata_path):
                with open(metadata_path) as f:
                    for line in f:
                        if ":" in line and "=" not in line:
                            k, v = line.strip().split(":", 1)
                            params[k.strip()] = v.strip()

            save_synthetic_results(results_traditional, results_tax, params, output_path)

            print(f"  Done: {dataset_folder}")

        except Exception as e:
            print(f" Error on {dataset_folder}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_all_methods()
