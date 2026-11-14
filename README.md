# Suicide Attempt Risk Calculator for Adolescents with Suicidal Ideation

A static web calculator for the final logistic regression model from:

> Machine Learning to Identify Adolescents With Suicidal Ideation at High Risk of Suicide Attempt: Development and Validation Study.

The full analysis code (data preparation, feature selection, model development and evaluation) is in [`analysis/`](analysis/).

The page runs entirely in the browser (HTML + JavaScript). There is no server; no data are sent or stored.

## What it does

- Takes the 18 model predictors (demographics, mental health, substance use, violence victimization, sexual behavior and sports-related concussion).
- Returns an estimated suicide attempt risk for adolescents who report serious suicidal ideation. It is classified against the F1-optimal threshold of 0.36.
- Shows a SHAP waterfall plot on the probability scale.
  - The SHAP values come from a permutation explainer with 300 antithetic permutations and a fixed seed.
  - The background sample is 200 observations from the training set.
- The Model Information tab lists the data source, test-set performance, limitations and model coefficients.

## Files

| File | Content |
|---|---|
| `index.html` | Page layout |
| `styles.css` | Styling |
| `app.js` | Inputs, rendering, waterfall plot |
| `calculator.js` | Prediction and permutation SHAP (also usable from Node) |
| `model.js` | Model parameters exported from the Python pipeline |
| `tools/export_web_model.py` | Script that generated `model.js` |
| `tools/verify.js` | Checks JavaScript predictions against scikit-learn |

## Verification

The JavaScript predictions were checked against scikit-learn `predict_proba` on all 2,948 test-set observations:

- **Maximum absolute difference:** 2.2 × 10⁻¹⁶.
- **Threshold classification:** agreed in 2,948 of 2,948 cases.

The SHAP values satisfy additivity: E[f(X)] + Σφ = f(x).

## Deploy on GitHub Pages

1. Create a repository on GitHub, for example `sa-risk-calculator`, and upload all files in this folder to the repository root. Include `.nojekyll`.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*.
4. Set **Branch** to `main` and the folder to `/ (root)`, then click **Save**.
5. After about one minute, the site is available at `https://<your-username>.github.io/sa-risk-calculator/`.

To use the calculator offline, open `index.html` directly in a browser. No build step is needed.

## Intended use

This calculator is for research use only.

- It estimates suicide attempt risk based on how closely an adolescent with suicidal ideation resembles ideators who have attempted suicide (cross-sectional training data).
- It has not been validated for predicting future attempts and does not replace clinical assessment.
- The model was developed with US high school students using self-reported survey data and has not been externally validated.

If someone is in immediate danger, call local emergency services. In the US, call or text 988 (Suicide & Crisis Lifeline).
