"""Sensitivity analysis: final LR (and XGB/LightGBM) refitted without suicide plan, same split (seed 20)."""
import json, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, f1_score, confusion_matrix
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
warnings.filterwarnings("ignore")

SEED, SPLIT_SEED = 2026, 20
from config import DERIVED as D, RESULTS
full = pd.read_csv(f"{D}/yrbs_ideators_imputed_full.csv")
strata = full["sa"].astype(int).astype(str) + "_" + full["year"].astype(str)
train, test = train_test_split(full, test_size=0.30, stratify=strata, random_state=SPLIT_SEED)
train = train.sort_values(["year", "record"]).reset_index(drop=True)
test = test.sort_values(["year", "record"]).reset_index(drop=True)
VARS_FULL = pd.read_csv(f"{D}/vars_selected.csv").variable.tolist()
BP = {r.model: json.loads(r.best_params) for r in pd.read_csv(f"{D}/best_params_train70.csv").itertuples()}
CAT_LEVELS = {"raceeth": ["White", "Asian", "Black", "Hispanic", "Other"], "nicotine_status": [0, 1, 2],
              "alcohol_status": [0, 1, 2], "marijuana_status": [0, 1, 2], "sexual_behavior": [0, 1, 2]}
y_tr, y_te = train.sa.astype(int).values, test.sa.astype(int).values
cv10 = StratifiedKFold(10, shuffle=True, random_state=SEED)


def pipe(vars_, est):
    cat = [c for c in CAT_LEVELS if c in vars_]; num = [v for v in vars_ if v not in cat]
    ohe = OneHotEncoder(categories=[CAT_LEVELS[c] for c in cat], drop="first", handle_unknown="ignore", sparse_output=False)
    return Pipeline([("prep", ColumnTransformer([("num", StandardScaler(), num), ("cat", ohe, cat)])), ("clf", est)])


def est(name, p):
    return {"LR": lambda: LogisticRegression(solver="liblinear", max_iter=5000, **p),
            "XGB": lambda: XGBClassifier(subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=-1, eval_metric="logloss", **p),
            "LightGBM": lambda: LGBMClassifier(learning_rate=0.05, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                               random_state=SEED, n_jobs=-1, verbose=-1, **p)}[name]()


def _midrank(x):
    J = np.argsort(x); Z = x[J]; N = len(x); T = np.zeros(N); i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]: j += 1
        T[i:j] = 0.5 * (i + j - 1) + 1; i = j
    out = np.empty(N); out[J] = T; return out


def delong(y, preds):
    y = np.asarray(y); o = np.argsort(-y); y = y[o]; preds = np.atleast_2d(preds)[:, o]
    m = int(y.sum()); n = len(y) - m
    tx = np.array([_midrank(r) for r in preds[:, :m]]); ty = np.array([_midrank(r) for r in preds[:, m:]])
    tz = np.array([_midrank(r) for r in preds])
    aucs = tz[:, :m].sum(1) / m / n - (m + 1.0) / 2.0 / n
    cov = np.cov((tz[:, :m] - tx) / n) / m + np.cov(1.0 - (tz[:, m:] - ty) / m) / n
    return aucs, np.atleast_2d(cov)


def auc_ci(y, p):
    a, c = delong(y, p[None, :]); se = np.sqrt(c[0, 0]); return a[0], a[0] - 1.96 * se, a[0] + 1.96 * se


def dl_test(y, p1, p2):
    a, c = delong(y, np.vstack([p1, p2])); z = (a[0] - a[1]) / np.sqrt(c[0, 0] + c[1, 1] - 2 * c[0, 1])
    return a[0] - a[1], 2 * stats.norm.sf(abs(z))


def hl(y, p, g=10):
    d = pd.DataFrame({"y": y, "p": p}); d["g"] = pd.qcut(d.p.rank(method="first"), g, labels=False)
    s = d.groupby("g").agg(o=("y", "sum"), e=("p", "sum"), n=("y", "size"))
    return stats.chi2.sf((((s.o - s.e) ** 2) / (s.e * (1 - s.e / s.n))).sum(), g - 2)


def f1_thr(y, p):
    g = np.round(np.arange(0.01, 1.0, 0.01), 2)
    return float(g[int(np.argmax([f1_score(y, (p >= t).astype(int)) for t in g]))])


def thr_metrics(y, p, t):
    tn, fp, fn, tp = confusion_matrix(y, (p >= t).astype(int)).ravel()
    return dict(Sensitivity=tp / (tp + fn), Specificity=tn / (tn + fp), PPV=tp / (tp + fp), NPV=tn / (tn + fn),
                F1=f1_score(y, (p >= t).astype(int)))


VARS_NP = [v for v in VARS_FULL if v != "plan"]
# Re-tune LR without plan using the same grid as the main analysis
gs = GridSearchCV(pipe(VARS_NP, LogisticRegression(solver="liblinear", max_iter=5000)),
                  {"clf__C": [0.01, 0.1, 1, 10, 100], "clf__penalty": ["l1", "l2"]}, scoring="roc_auc", cv=cv10, n_jobs=-1)
gs.fit(train[VARS_NP], y_tr)
lr_np = {k.replace("clf__", ""): v for k, v in gs.best_params_.items()}
print("LR (no plan) best params", lr_np)

rows, preds = [], {}
for name in ["LR", "XGB", "LightGBM"]:
    for label, vars_, p in [("With suicide plan", VARS_FULL, BP[name]),
                            ("Without suicide plan", VARS_NP, lr_np if name == "LR" else BP[name])]:
        pcv = cross_val_predict(pipe(vars_, est(name, p)), train[vars_], y_tr, cv=cv10, method="predict_proba")[:, 1]
        pte = pipe(vars_, est(name, p)).fit(train[vars_], y_tr).predict_proba(test[vars_])[:, 1]
        preds[(name, label)] = pte
        t = f1_thr(y_tr, pcv)
        a, lo, hi = auc_ci(y_te, pte)
        ac, lc, hc = auc_ci(y_tr, pcv)
        rows.append({"Model": name, "Predictors": label, "n predictors": len(vars_),
                     "Training CV AUC (95% CI)": f"{ac:.3f} ({lc:.3f}-{hc:.3f})",
                     "Test AUC (95% CI)": f"{a:.3f} ({lo:.3f}-{hi:.3f})", "F1-optimal threshold": t,
                     **{k: round(v, 3) for k, v in thr_metrics(y_te, pte, t).items()},
                     "H-L p": round(hl(y_te, pte), 3), "Brier": round(brier_score_loss(y_te, pte), 3)})
res = pd.DataFrame(rows)
dl = []
for name in ["LR", "XGB", "LightGBM"]:
    d, pv = dl_test(y_te, preds[(name, "With suicide plan")], preds[(name, "Without suicide plan")])
    dl.append({"Model": name, "AUC difference (with - without)": round(d, 3), "DeLong p": pv})
dl = pd.DataFrame(dl)
pd.set_option("display.width", 250, "display.max_columns", 30)
print(res.to_string(index=False)); print(dl.to_string(index=False))
res.to_csv(RESULTS / "sensitivity_no_plan.csv", index=False)
dl.to_csv(RESULTS / "sensitivity_no_plan_delong.csv", index=False)
json.dump(lr_np, open(RESULTS / "sensitivity_no_plan_LR_params.json", "w"))
