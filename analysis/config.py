"""Shared paths. Place the CDC national YRBS files (2019, 2021, 2023, 2025) in data/raw/:
XXH{year}_YRBS_Data.dat, {year}XXH-SAS-Input-Program.sas and {year}XXH-Formats-Program.sas."""
from pathlib import Path
import os

ROOT = Path(os.environ.get("YRBS_SA_ROOT", Path(__file__).resolve().parent))
RAW = ROOT / "data" / "raw"          # CDC files (not distributed here)
WORK = ROOT / "data" / "work"        # intermediate files
DERIVED = ROOT / "data" / "derived"  # analytic data sets
RESULTS = ROOT / "results"           # tables, figures and model outputs
for p in (WORK, DERIVED, RESULTS):
    p.mkdir(parents=True, exist_ok=True)

YEARS = [2019, 2021, 2023, 2025]
SPLIT_SEED = 20      # random_state of the stratified 70/30 split
SEED = 2026          # all other random processes (imputation, cross-validation, models)
