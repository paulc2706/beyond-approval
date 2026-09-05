import os
import sys
import traceback
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Real-world Simulations", "Traditional Methods"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Real-world Simulations", "Tax Methods"))
from synthetic_methods import sample_resampling, sample_euclidean_threshold, sample_impartial, save_synthetic_dataset

output_folder = str(Path(__file__).resolve().parents[1] / "Data" / "Synthetic Data")

NUM_Voters = 100
NUM_Candidates = 20
P_Disapprove = 0.2

P_Values = [0.1, 0.15, 0.3, 0.5, 0.7]
PHI_Values = [0.25, 0.5, 0.75, 1]
Euclidean_Radius = [1.5, 2, 3, 4]
SEED = 42

def generate_resampling_datasets():
    #Loops over all combinations of approval probabilities (p) and dispersion parameters (phi)
    for p in P_Values:
        for phi in PHI_Values:
            label = f"resampling_p{p}_phi{phi}"
            print(f"\n{"=" * 50}")
            print(f"Generating: {label}")

            try:
                _, _, votes = sample_resampling(NUM_Voters, NUM_Candidates, p=p, phi=phi, p_disapprove=P_Disapprove, seed=SEED)
                #Bundles active parameters to be saved alongside the data as reference metadata
                params = {
                    "Model": "Resampling",
                    "p": p, "phi": phi,
                    "p_disapprove": P_Disapprove,
                    "num_voters": NUM_Voters,
                    "num_candidates": NUM_Candidates,
                }
                output_path = os.path.join(output_folder, label)
                save_synthetic_dataset(votes, params, output_path)

            except Exception as e:
                print(f"Error generating: {label}: {e}")
                traceback.print_exc()

def generate_impartial_datasets():
    for p in P_Values:
        label = f"impartial_p{p}"
        print(f"\n{"=" * 50}")
        print(f"Generating: {label}")

        try:
            _, _, votes = sample_impartial(NUM_Voters, NUM_Candidates, p=p, p_disapprove=P_Disapprove, seed=SEED)
            params = {
                "Model": "Impartial",
                "p": p,
                "p_disapprove": P_Disapprove,
                "num_voters": NUM_Voters,
                "num_candidates": NUM_Candidates,
            }
            output_path = os.path.join(output_folder, label)
            save_synthetic_dataset(votes, params, output_path)

        except Exception as e:
            print(f"Error generating: {label}: {e}")
            traceback.print_exc()

def generate_euclidean_dataset():
    for radius in Euclidean_Radius:
        label = f"euclidean_r{radius}"
        print(f"\n{"=" * 50}")
        print(f"Generating: {label}")

        try:
            _, _, votes = sample_euclidean_threshold(NUM_Voters, NUM_Candidates, radius=radius, p_disapprove=P_Disapprove, seed=SEED)
            params = {
                "Model": "Euclidean2D",
                "radius": radius,
                "p_disapprove": P_Disapprove,
                "num_voters": NUM_Voters,
                "num_candidates": NUM_Candidates,
            }
            output_path = os.path.join(output_folder, label)
            save_synthetic_dataset(votes, params, output_path)

        except Exception as e:
            print(f"Error generating: {label}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    generate_resampling_datasets()
    generate_impartial_datasets()
    generate_euclidean_dataset()