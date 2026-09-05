# Disapproval-Extended ABC Voting Rules — Simulation Pipeline

Code accompanying the Bachelor's thesis on disapproval-extended approval-based
committee (ABC) voting rules. It runs traditional ABC rules (PAV, seq-Phragmen,
MES, AV) and their tax-extended counterparts (TaxPhragmen, TaxMES) against
real-world Polis datasets and synthetically generated approval/disapproval
profiles, then computes comparison metrics, statistical tests, and plots.

## Requirements

- Python 3.11+ (some scripts use nested-quote f-strings, a 3.12+ language
  feature — developed and tested on 3.13)
- A [Gurobi](https://www.gurobi.com/) license for `abcvoting`'s optimization
  backend — a free [Gurobi academic/educational license](https://www.gurobi.com/academia/academic-program-and-licenses/)
  works. A size-limited license (e.g. the default trial/community license)
  will fail on larger real-world datasets with
  `GurobiError: Model too large for size-limited license`.

Install dependencies:

```bash
pip install -r requirements.txt
```

`matplotlib` is pinned to a pre-release version (`3.11.0rc1`); if `pip`
refuses it, either add `--pre` or relax the pin to the latest stable release.
`pingouin` is left unpinned — pin it yourself once you know the version you
use (`pip show pingouin`).

## Project layout

```
Data/
  Real-World/openData-master/        Polis export datasets (one folder per dataset)
  Synthetic Data/pd_<value>/          Synthetic datasets, one folder per disapproval
                                       probability, sampler-named subfolders inside
Results/
  Results Real-World/                 Simulation output, mirrors Data/Real-World structure
  Results Synthetic/pd_<value>/       Simulation output, mirrors Data/Synthetic Data structure

Real-world Simulations/
  Traditional Methods/                PAV, seq-Phragmen, MES, AV
  Tax Methods/                        TaxPhragmen, TaxMES

Synthetic Simulations/                Synthetic data generation + simulation runners

Metrics, Tests & Plots/
  Metrics/                            Per-rule/per-dataset metric computation
  Statistical Tests/                  Hamming-distance group comparisons (ANOVA/Welch)
  Visualizations/                     All plots for the thesis
```

Each stage follows a runner/methods split: a `*_methods.py` file holds pure
functions with no file paths or execution logic, and a `run_*.py` file holds
the parameters, paths, and the actual execution. Path resolution is
self-contained — every runner computes its own project root from its file
location (`Path(__file__).resolve().parents[N]`), so nothing needs to be
configured or edited to run the pipeline after cloning; it works from any
location on any OS as long as the folder structure above stays intact.

## Running the pipeline

Run in this order — later stages read the previous stage's output:

1. **Real-world simulations** (`Real-world Simulations/`)
   - `Traditional Methods/run_sim_batch.py` — runs PAV/seq-Phragmen/MES/AV on
     every dataset under `Data/Real-World/openData-master/`, writes to
     `Results/Results Real-World/<dataset>/`
   - `Tax Methods/run_tax_batch.py` — same, for TaxPhragmen/TaxMES
   - `run_sim_single.py` / `run_tax_single.py` run a single hardcoded dataset
     (`american-assembly.bowling-green`) for quick manual testing

2. **Synthetic data + simulations** (`Synthetic Simulations/`)
   - `run_synthetic_sampling.py` generates synthetic profiles (resampling,
     impartial culture, Euclidean threshold models) into
     `Data/Synthetic Data/`. `P_Disapprove` at the top of the file is a single
     hardcoded constant, not a loop — to generate the datasets for the next
     `pd` level (0.01, 0.05, 0.1, 0.15, 0.2), you must manually edit
     `P_Disapprove` and rerun the script. Output is **not** namespaced by
     `pd` value (it always writes to the same sampler-named subfolders under
     `Data/Synthetic Data/`), so move the batch you just generated into its
     `pd_<value>` folder **before** rerunning with a new `P_Disapprove` —
     otherwise the next run silently overwrites it.
   - `run_synthetic_experiments.py` runs all traditional and tax methods over
     every `pd_<value>` folder found under `Data/Synthetic Data/`, writing to
     `Results/Results Synthetic/pd_<value>/`

3. **Metrics** (`Metrics, Tests & Plots/Metrics/`)
   - `run_metrics.py` computes per-rule metrics (net score, voter utility,
     Gini coefficient, disapproval avoidance, Hamming distances) for both
     real-world and synthetic results, writing `metrics_real_world.csv` and
     `metrics_synthetic.csv`
   - `generate_metrics_overview.py`, `correlation_test.py`, `run_stats_test.py`
     are secondary analyses that read those two CSVs

4. **Statistical tests** (`Metrics, Tests & Plots/Statistical Tests/`)
   - `run_statistical_tests.py` — the Hamming-distance group comparisons
     (Levene → one-way ANOVA/Tukey or Welch/Games-Howell depending on
     variance homogeneity) reported in the thesis, on both real-world and
     synthetic data

5. **Visualizations** (`Metrics, Tests & Plots/Visualizations/`)
   - `run_visualizations.py` regenerates every plot used in the thesis from
     the two metrics CSVs, into `Visualizations/Plots/`

Each script can be re-run independently as long as the CSVs/results it reads
already exist from an earlier stage.

