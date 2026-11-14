"""Final LR model coefficients on the original predictor scale, with bootstrap 95% CIs (training set, seed-20 split)."""
import json, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from config import DERIVED as D, RESULTS
full = pd.read_csv(f"{D}/yrbs_ideators_imputed_full.csv")
strata = full["sa"].astype(int).astype(str) + "_" + full["year"].astype(str)
train, _ = train_test_split(full, test_size=0.30, stratify=strata, random_state=20)
train = train.sort_values(["year", "record"]).reset_index(drop=True)
VARS = pd.read_csv(f"{D}/vars_selected.csv").variable.tolist()
BP = {r.model: json.loads(r.best_params) for r in pd.read_csv(f"{D}/best_params_train70.csv").itertuples()}["LR"]
CAT = {"raceeth": ["White", "Asian", "Black", "Hispanic", "Other"], "nicotine_status": [0, 1, 2],
       "alcohol_status": [0, 1, 2], "marijuana_status": [0, 1, 2], "sexual_behavior": [0, 1, 2]}
cat = [c for c in CAT if c in VARS]; num = [v for v in VARS if v not in cat]
y = train.sa.astype(int).values


def fit_raw(df, yy):
    pre = ColumnTransformer([("num", StandardScaler(), num),
                             ("cat", OneHotEncoder(categories=[CAT[c] for c in cat], drop="first", sparse_output=False), cat)])
    m = Pipeline([("prep", pre), ("clf", LogisticRegression(solver="liblinear", max_iter=5000, **BP))]).fit(df[VARS], yy)
    sc = m.named_steps["prep"].named_transformers_["num"]; clf = m.named_steps["clf"]
    b = clf.coef_[0]; bn, bc = b[:len(num)], b[len(num):]
    raw_num = bn / sc.scale_
    b0 = clf.intercept_[0] - np.sum(bn * sc.mean_ / sc.scale_)
    return np.concatenate([[b0], raw_num, bc])


names = ["Intercept"] + num + [f"{c}={lvl}" for c in cat for lvl in CAT[c][1:]]
est = fit_raw(train, y)
rng = np.random.default_rng(2026); B = 1000; boot = np.empty((B, len(est)))
for i in range(B):
    idx = rng.integers(0, len(train), len(train))
    boot[i] = fit_raw(train.iloc[idx], y[idx])
lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
out = pd.DataFrame({"term": names, "beta": est, "lo": lo, "hi": hi})
out.to_csv(RESULTS / "lr_final_coefficients.csv", index=False)
print("params", BP); print(out.round(3).to_string(index=False))
