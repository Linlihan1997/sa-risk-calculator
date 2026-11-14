"""Export the final LR model (seed-20 training fit) to JSON for the static web calculator."""
import json, warnings, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings("ignore")

import sys, pathlib
REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "analysis"))
from config import DERIVED as D, RESULTS
OUT = REPO   # web calculator files are written to the repository root
full = pd.read_csv(f"{D}/yrbs_ideators_imputed_full.csv")
strata = full["sa"].astype(int).astype(str) + "_" + full["year"].astype(str)
train, test = train_test_split(full, test_size=0.30, stratify=strata, random_state=20)
train = train.sort_values(["year", "record"]).reset_index(drop=True)
test = test.sort_values(["year", "record"]).reset_index(drop=True)
VARS = pd.read_csv(f"{D}/vars_selected.csv").variable.tolist()
BP = {r.model: json.loads(r.best_params) for r in pd.read_csv(f"{D}/best_params_train70.csv").itertuples()}["LR"]
CAT = {"raceeth": ["White", "Asian", "Black", "Hispanic", "Other"], "nicotine_status": [0, 1, 2],
       "alcohol_status": [0, 1, 2], "marijuana_status": [0, 1, 2], "sexual_behavior": [0, 1, 2]}
cat = [c for c in CAT if c in VARS]; num = [v for v in VARS if v not in cat]
pre = ColumnTransformer([("num", StandardScaler(), num),
                         ("cat", OneHotEncoder(categories=[CAT[c] for c in cat], drop="first", sparse_output=False), cat)])
m = Pipeline([("prep", pre), ("clf", LogisticRegression(solver="liblinear", max_iter=5000, **BP))]).fit(train[VARS], train.sa.astype(int))
sc = m.named_steps["prep"].named_transformers_["num"]; clf = m.named_steps["clf"]
coef = clf.coef_[0]; k = len(num)
model = {
    "intercept": float(clf.intercept_[0]),
    "numeric": [{"var": v, "mean": float(sc.mean_[i]), "scale": float(sc.scale_[i]), "coef": float(coef[i])} for i, v in enumerate(num)],
    "categorical": [], "threshold": 0.36, "vars": VARS,
}
j = k
for c in cat:
    levels = CAT[c]; coefs = {str(levels[0]): 0.0}
    for lvl in levels[1:]:
        coefs[str(lvl)] = float(coef[j]); j += 1
    model["categorical"].append({"var": c, "reference": str(levels[0]), "coefs": coefs})

rng = np.random.default_rng(2026)
bg = train.iloc[rng.choice(len(train), 200, replace=False)][VARS].copy()
bg["raceeth"] = bg["raceeth"].astype(str)
model["background"] = [{v: (r[v] if v == "raceeth" else int(r[v])) for v in VARS} for _, r in bg.iterrows()]
p_bg = m.predict_proba(bg[VARS])[:, 1]
model["base_value"] = float(p_bg.mean())

json.dump(model, open(f"{OUT}/model.json", "w"), indent=1)
# verification cases: all test rows with sklearn probabilities
ver = test[VARS].copy(); ver["p_sklearn"] = m.predict_proba(test[VARS])[:, 1]
ver.to_csv(RESULTS / "verify_test_rows.csv", index=False)

# Python permutation SHAP for two cases, same background, for cross-checking the JS implementation
import shap
RC = CAT["raceeth"]
def enc(df):
    d = df.copy(); d["raceeth"] = d["raceeth"].map({r: i for i, r in enumerate(RC)}); return d.astype(float).values
def f(X):
    d = pd.DataFrame(X, columns=VARS); d["raceeth"] = d["raceeth"].round().astype(int).map(dict(enumerate(RC)))
    return m.predict_proba(d)[:, 1]
expl = shap.explainers.Permutation(f, enc(bg[VARS]), seed=2026)
cases = test.iloc[[0, 5]][VARS]
sv = expl(enc(cases), max_evals=4000)
pd.DataFrame(sv.values, columns=VARS).assign(base=sv.base_values).to_csv(RESULTS / "verify_shap_python.csv", index=False)
cases.to_csv(RESULTS / "verify_shap_cases.csv", index=False)
print("intercept", model["intercept"], "base", model["base_value"], "n_num", k, "n_cat", len(cat))
