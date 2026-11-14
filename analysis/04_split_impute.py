"""Stratified 70/30 split of the pooled 2019-2025 sample (by outcome x survey year) and random forest-based
iterative imputation fitted on the training set only (the outcome is not used) and applied to the test set.
Outputs: data/derived/train_70_imputed.csv, test_30_imputed.csv and yrbs_ideators_imputed_full.csv (both sets combined)."""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor

from config import DERIVED as OUT, SEED, SPLIT_SEED
raw = pd.read_csv(OUT / "analytic_sample_composites_unimputed.csv")
ID = ["year", "record", "weight", "weight_pooled", "stratum_u", "psu_u", "sa_times", "sa"]
cands = [c for c in raw.columns if c not in ID]
imp_cols = [c for c in cands if c != "raceeth"]

strat = raw.sa.astype(int).astype(str) + "_" + raw.year.astype(str)
tr, te = train_test_split(raw, test_size=0.30, stratify=strat, random_state=SPLIT_SEED)
tr, te = tr.sort_values(["year", "record"]).copy(), te.sort_values(["year", "record"]).copy()

rf = RandomForestRegressor(n_estimators=40, max_depth=12, min_samples_leaf=5, n_jobs=-1, random_state=SEED)
imp = IterativeImputer(estimator=rf, max_iter=5, initial_strategy="most_frequent", random_state=SEED, skip_complete=True)
imp.fit(tr[imp_cols])
rng = {c: (np.nanmin(tr[c]), np.nanmax(tr[c])) for c in imp_cols}
mode_race = tr.raceeth.mode()[0]


def apply(df):
    x = pd.DataFrame(imp.transform(df[imp_cols]), columns=imp_cols, index=df.index)
    for c in imp_cols:
        miss = df[c].isna()
        v = x[c].clip(*rng[c])
        if c != "bmi":
            v = v.round()
        x[c] = df[c].where(~miss, v)          # only imputed cells are clipped/rounded
        if c != "bmi":
            x[c] = x[c].astype(int)
    out = pd.concat([df[ID], df[["raceeth"]].fillna(mode_race), x], axis=1)
    return out[ID + cands]


trI, teI = apply(tr), apply(te)
assert trI[cands].isna().sum().sum() == 0 and teI[cands].isna().sum().sum() == 0
for c in imp_cols:   # observed values untouched
    assert ((trI[c] != tr[c]) & tr[c].notna()).sum() == 0 and ((teI[c] != te[c]) & te[c].notna()).sum() == 0
trI.to_csv(f"{OUT}/train_70_imputed.csv", index=False, encoding="utf-8-sig")
teI.to_csv(f"{OUT}/test_30_imputed.csv", index=False, encoding="utf-8-sig")
pd.concat([trI, teI]).sort_values(["year", "record"]).to_csv(f"{OUT}/yrbs_ideators_imputed_full.csv",
                                                          index=False, encoding="utf-8-sig")
summ = pd.DataFrame({"set": ["train", "test"], "n": [len(trI), len(teI)], "attempts": [int(trI.sa.sum()), int(teI.sa.sum())],
                     "prevalence": [round(trI.sa.mean(), 4), round(teI.sa.mean(), 4)],
                     "cells_imputed": [int(tr[cands].isna().sum().sum()), int(te[cands].isna().sum().sum())]})
print(summ.to_string()); print(pd.crosstab(pd.concat([trI.assign(s="train"), teI.assign(s="test")]).year,
                                         pd.concat([trI.assign(s="train"), teI.assign(s="test")]).s))
