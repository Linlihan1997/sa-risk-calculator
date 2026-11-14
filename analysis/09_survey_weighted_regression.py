"""Survey-weighted multivariable logistic regression of suicide attempt among ideators (full sample, n = 9,824).
Point estimates: weighted maximum likelihood. Variance: Taylor linearization with strata and PSUs (with-replacement),
single-PSU strata centred on the overall mean (as survey::options(survey.lonely.psu = "adjust")). t-based CIs, df = #PSU - #strata."""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats

from config import DERIVED, RESULTS
d = pd.read_csv(DERIVED / "yrbs_ideators_imputed_full.csv")
CAT = {"raceeth": ["White", "Black", "Hispanic", "Asian", "Other"], "nicotine_status": [0, 1, 2],
       "alcohol_status": [0, 1, 2], "marijuana_status": [0, 1, 2], "sexual_behavior": [0, 1, 2]}
CAND = ["age", "grade", "female", "raceeth", "sexual_minority", "bmi", "sad_hopeless", "plan", "sleep_hours",
        "nicotine_status", "alcohol_status", "marijuana_status", "other_drug_any", "early_onset_any", "bullying_count",
        "school_victim_any", "fighting_any", "weapon_any", "sexual_dating_violence_any", "sexual_behavior",
        "fv_none_count", "no_breakfast", "drank_soda", "pa_5days", "sports_pe_any", "concussion", "dentist", "hiv_std_test_any"]
FINAL18 = pd.read_csv(DERIVED / "vars_selected.csv").variable.tolist()


def design(vars_):
    cols = {}
    for v in vars_:
        if v in CAT:
            for lvl in CAT[v][1:]:
                cols[f"{v}={lvl}"] = (d[v].astype(str) == str(lvl)).astype(float)
        else:
            cols[v] = d[v].astype(float)
    X = pd.DataFrame(cols); X.insert(0, "const", 1.0); return X


def svy_logit(vars_):
    X = design(vars_); y = d.sa.astype(float).values; w = d.weight_pooled.values
    fit = sm.GLM(y, X, family=sm.families.Binomial(), freq_weights=w).fit()
    b = fit.params.values; p = 1 / (1 + np.exp(-X.values @ b))
    H = (X.values * (w * p * (1 - p))[:, None]).T @ X.values; Hinv = np.linalg.inv(H)
    U = X.values * (w * (y - p))[:, None]                         # score contributions
    df_ = pd.DataFrame(U); df_["psu"] = d.psu_u.values; df_["str"] = d.stratum_u.values
    Z = df_.groupby(["str", "psu"]).sum()                          # PSU totals
    meat = np.zeros((X.shape[1], X.shape[1])); grand = Z.values.mean(axis=0)
    for s, g in Z.groupby(level=0):
        n_h = len(g); zz = g.values
        if n_h == 1:
            e = zz - grand; meat += e.T @ e                        # lonely PSU: centre on overall mean
        else:
            e = zz - zz.mean(axis=0); meat += n_h / (n_h - 1) * (e.T @ e)
    V = Hinv @ meat @ Hinv; se = np.sqrt(np.diag(V))
    dfree = d.psu_u.nunique() - d.stratum_u.nunique(); tq = stats.t.ppf(0.975, dfree)
    out = pd.DataFrame({"term": X.columns, "beta": b, "se": se})
    out["aOR"] = np.exp(out.beta); out["lo"] = np.exp(out.beta - tq * out.se); out["hi"] = np.exp(out.beta + tq * out.se)
    out["p"] = 2 * stats.t.sf(np.abs(out.beta / out.se), dfree)
    # unweighted model-based check for orientation
    unw = sm.GLM(y, X, family=sm.families.Binomial()).fit()
    out["aOR_unweighted"] = np.exp(unw.params.values)
    return out, dfree


res28, dfree = svy_logit(CAND)
res18, _ = svy_logit(FINAL18)
# VIF for the 28-candidate design
from statsmodels.stats.outliers_influence import variance_inflation_factor
X = design(CAND); vif = pd.Series([variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])], index=X.columns[1:])
pd.set_option("display.width", 200)
print("df =", dfree, "| max VIF (28-candidate design) =", round(vif.max(), 2), vif.idxmax())
print(res28.round(3).to_string(index=False))
res28.to_csv(RESULTS / "risk_factors_weighted_28.csv", index=False)
res18.to_csv(RESULTS / "risk_factors_weighted_18.csv", index=False)
