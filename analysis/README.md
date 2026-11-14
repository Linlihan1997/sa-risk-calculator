# Analysis code

Code for the study *Machine Learning to Identify Adolescents With Suicidal Ideation at High Risk of Suicide Attempt:
Development and Validation Study* (US national Youth Risk Behavior Survey [YRBS] 2019–2025).

## Data

The national YRBS data are publicly available from the US Centers for Disease Control and Prevention
(https://www.cdc.gov/yrbs/data/index.html) and are not redistributed here. Download the 2019, 2021, 2023 and 2025
files and place them in `analysis/data/raw/`:

- `XXH{year}_YRBS_Data.dat`
- `{year}XXH-SAS-Input-Program.sas`
- `{year}XXH-Formats-Program.sas`

## Software

Python 3.13 (packages in `requirements.txt`) and R 4.3.3 (glmnet 4.1.8, Boruta 8.0.0, car 3.1.2, ggplot2, ggridges).

## Steps

Run from the `analysis/` folder, in order.

| Step | File | Content |
|---|---|---|
| 1 | `01_load_yrbs.py` | Read the CDC fixed-width files using the CDC SAS input programs |
| 2 | `02_harmonize.py` | Harmonize items across survey years; select adolescents aged 14–17 years with serious suicidal ideation (n = 9824) |
| 3 | `03_build_composites.py` | Build composite candidate predictors; exclude candidates with >20% missing data |
| 4 | `04_split_impute.py` | Stratified 70/30 split (by outcome and survey year); random forest–based imputation fitted on the training set only |
| 5 | `05_feature_selection.R` | LASSO (10-fold CV, λ1se) and Boruta in the training set; final predictors = selected by both; VIF |
| 6 | `06_model_development.ipynb` | Eight algorithms, hyperparameters, test set evaluation (discrimination, calibration, DeLong tests), PPV/NPV by prevalence, decision curve analysis, SHAP, flowchart |
| 7 | `07_sensitivity_no_plan.py` | Sensitivity analysis without suicide plan |
| 8 | `08_lr_coefficients.py` | Coefficients of the final logistic regression model on the original scale, with bootstrap 95% CIs |
| 9 | `09_survey_weighted_regression.py` | Secondary analysis: survey-weighted multivariable logistic regression of all 28 candidates |
| 10 | `10_figure2_feature_selection.R` | Figure 2 (LASSO paths, cross-validation curve and Boruta importance) |

Hyperparameters are fixed in the notebook; set `RUN_TUNING = True` in the notebook to repeat the grid search.
The web calculator in the repository root is generated from the final model by `tools/export_web_model.py`.
Outputs are written to `analysis/results/`.

Steps 1–4 were re-run from the original CDC files to confirm that they reproduce the analytic data sets used in the paper.
