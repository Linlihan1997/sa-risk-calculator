"""Collapse related YRBS items into composite candidate predictors and apply the missing-data rule.

Composite rules
  status (0/1/2): 2 = used in the past 30 days; 1 = ever used but not in the past 30 days; 0 = never used.
  any:  1 if any component = 1; 0 if no component = 1 and at least half of the components were answered; otherwise missing.
  count: sum of components, requires all components answered.
Candidates with >20% missing data in the pooled sample are excluded.
Output: data/derived/analytic_sample_composites_unimputed.csv (imputation is done after the split, in step 04).
"""
import os, pickle, time
import numpy as np
import pandas as pd

from config import WORK as W, DERIVED, RESULTS, YEARS
MISS_MAX = 20.0
a = pd.read_pickle(f"{W}/analytic_raw.pkl").reset_index(drop=True)


def any_of(cols):
    x = a[cols]
    res = pd.Series(np.nan, index=a.index)
    answered = x.notna().sum(axis=1)
    res[(answered >= np.ceil(len(cols) / 2)) & ~(x == 1).any(axis=1)] = 0
    res[(x == 1).any(axis=1)] = 1
    return res


def status(ever_flags, current_flags):
    """ever_flags / current_flags: lists of Series with 1/0/NaN."""
    ever = pd.concat(ever_flags, axis=1); cur = pd.concat(current_flags, axis=1)
    res = pd.Series(np.nan, index=a.index)
    never = (ever == 0).any(axis=1) & ~(ever == 1).any(axis=1) & ~(cur == 1).any(axis=1)
    res[never] = 0
    cur_answered = cur.notna().sum(axis=1) >= np.ceil(cur.shape[1] / 2)
    res[(ever == 1).any(axis=1) & ~(cur == 1).any(axis=1) & cur_answered] = 1
    res[(cur == 1).any(axis=1)] = 2
    return res


def init_ever(col):   # initiation item: 1 = never, 2..7 = age band of first use
    return a[col].map(lambda v: np.nan if pd.isna(v) else (0 if v == 1 else 1))


def init_before13(col):
    return a[col].map(lambda v: np.nan if pd.isna(v) else (1 if v in (2, 3, 4) else 0))


C = {}   # name -> (series, label, domain, type, component items, rule)
def add(name, s, label, dom, typ, comp, rule):
    C[name] = (s, label, dom, typ, comp, rule)

add("age", a.age, "Age", "Demographics", "continuous", "Q1", "years (14-17)")
add("grade", a.grade, "Grade", "Demographics", "ordinal", "Q3", "9-12")
add("female", a.female, "Female sex", "Demographics", "binary", "Q2", "1 = female")
add("raceeth", a.raceeth, "Race/ethnicity", "Demographics", "categorical (5)", "RACEETH",
    "White/Black/Hispanic/Asian/Other; one-hot encoded for modelling")
add("sexual_minority", a.sexual_minority, "Sexual minority", "Demographics", "binary", "sexual identity",
    "gay or lesbian, bisexual, other or questioning = 1")
add("bmi", a.bmi, "BMI", "Body weight", "continuous", "height, weight", "kg/m2")
add("weight_concern", any_of(["perceive_overweight", "trying_lose_weight"]), "Weight concern", "Body weight", "binary",
    "perceived overweight; trying to lose weight", "any = 1")
add("sad_hopeless", a.sad_hopeless, "Persistent sadness or hopelessness", "Mental health", "binary",
    "sad or hopeless", ">=2 weeks")
add("sleep_hours", a.sleep_hours, "Sleep hours on school nights", "Sleep", "ordinal", "sleep", "4-10 hours")

nic_ever = [a.ever_cig, init_ever("cig_init"), a.ever_evp]
nic_cur = [a.current_cig, a.current_evp, a.smokeless, a.cigar]
add("nicotine_status", status(nic_ever, nic_cur), "Tobacco/nicotine use", "Substance use", "ordinal (0/1/2)",
    "ever smoked; age at first cigarette; ever vaped; current cigarette, e-cigarette, smokeless tobacco or cigar use",
    "0 = never, 1 = former (not in past 30 days), 2 = current (past 30 days)")
add("alcohol_status", status([init_ever("alc_init")], [a.current_alcohol]), "Alcohol use", "Substance use",
    "ordinal (0/1/2)", "age at first drink; current drinking", "0 = never, 1 = former, 2 = current")
add("marijuana_status", status([a.ever_marijuana, init_ever("mj_init")], [a.current_marijuana]), "Marijuana use",
    "Substance use", "ordinal (0/1/2)", "ever used; age at first use; current use", "0 = never, 1 = former, 2 = current")
add("other_drug_any", any_of(["ever_cocaine", "ever_inhalants", "ever_heroin", "ever_meth", "ever_ecstasy",
                              "ever_hallucinogen", "ever_inject", "ever_rx_pain_misuse"]),
    "Illicit drug use or prescription opioid misuse (lifetime)", "Substance use", "binary",
    "cocaine; inhalants; heroin; methamphetamine; ecstasy; hallucinogens; injection; prescription pain medicine misuse",
    "any = 1")
early = pd.concat([init_before13("cig_init"), init_before13("alc_init"), init_before13("mj_init")], axis=1)
early.columns = ["c", "al", "m"]
a["_e_c"], a["_e_al"], a["_e_m"] = early.c, early.al, early.m
add("early_onset_any", any_of(["_e_c", "_e_al", "_e_m"]), "Substance use before age 13", "Substance use", "binary",
    "age at first cigarette, drink and marijuana use", "any before 13 = 1")

bully = a[["bullied_school", "ebullied"]]
add("bullying_count", bully.sum(axis=1, min_count=2), "Bullying victimization (number of types)",
    "Violence and safety", "count (0-2)", "bullied on school property; electronically bullied", "0, 1 or 2")
add("school_victim_any", any_of(["unsafe_school", "threatened_weapon_school"]),
    "School violence victimization or feeling unsafe", "Violence and safety", "binary",
    "missed school because unsafe; threatened or injured with a weapon at school", "any = 1")
add("fighting_any", any_of(["fight", "fight_school"]), "Physical fighting", "Violence and safety", "binary",
    "physical fight; fight on school property", "any = 1")
add("weapon_any", any_of(["weapon_school", "gun"]), "Weapon carrying", "Violence and safety", "binary",
    "weapon on school property; gun", "any = 1")
add("sexual_dating_violence_any", any_of(["forced_sex", "sexual_violence", "sexual_dating_violence",
                                         "physical_dating_violence"]),
    "Sexual or dating violence victimization", "Violence and safety", "binary",
    "forced intercourse; sexual violence; sexual dating violence; physical dating violence", "any = 1")

sx = pd.Series(np.nan, index=a.index)
sx[a.ever_sex == 0] = 0
sx[(a.ever_sex == 1) | (a.currently_sex_active == 1)] = 1
sx[(a.sex_before13 == 1) | (a.sex_4plus == 1)] = 2
add("sexual_behavior", sx, "Sexual behavior", "Sexual behavior", "ordinal (0/1/2)",
    "ever had sex; currently sexually active; first sex before 13; >=4 partners",
    "0 = never, 1 = ever without high-risk feature, 2 = first sex before 13 or >=4 partners")

fv = a[["no_fruit", "no_salad", "no_potato", "no_carrot", "no_other_veg"]]
add("fv_none_count", (fv.mean(axis=1) * 5).where(fv.notna().sum(axis=1) >= 3).round(),
    "Fruit/vegetable types not eaten in past 7 days", "Diet", "count (0-5)",
    "fruit; salad; potatoes; carrots; other vegetables", "rescaled when >=3 items answered")
add("no_breakfast", a.no_breakfast, "No breakfast in past 7 days", "Diet", "binary", "breakfast", "")
add("drank_soda", 1 - a.no_soda, "Soda consumption in past 7 days", "Diet", "binary", "soda", "")
add("pa_5days", a.pa_5days, "Physically active >=60 min on >=5 days/week", "Physical activity", "binary",
    "physical activity", "")
add("sports_pe_any", any_of(["sports_team", "pe_1day"]), "Sports team or PE participation", "Physical activity",
    "binary", "sports team; physical education", "any = 1")
add("concussion", a.concussion, "Sports-related concussion", "Health", "binary", "concussion", "")
add("dentist", a.dentist, "Dental visit in past 12 months", "Health services", "binary", "dentist", "")
add("hiv_std_test_any", any_of(["hiv_test", "std_test"]), "Ever tested for HIV or STD", "Health services", "binary",
    "HIV test; STD test", "any = 1")
add("difficulty_concentrating", a.difficulty_concentrating, "Serious difficulty concentrating, remembering or deciding",
    "Mental health", "binary", "difficulty concentrating", "")
add("english_well", a.english_well, "Speaks English well", "Demographics", "binary", "English proficiency", "")
add("muscle_3days", a.muscle_3days, "Muscle strengthening on >=3 days/week", "Physical activity", "binary",
    "muscle strengthening", "")
add("drinks_10plus", a.drinks_10plus, "Largest number of drinks in a row >=10", "Substance use", "binary",
    "largest number of drinks", "")

X = pd.DataFrame({k: v[0] for k, v in C.items()})
rows = []
for k, (s, label, dom, typ, comp, rule) in C.items():
    miss_year = {y: round(s[a.year == y].isna().mean() * 100, 1) for y in YEARS}
    miss = round(s.isna().mean() * 100, 1)
    rows.append({"variable": k, "label": label, "domain": dom, "type": typ, "components": comp, "rule": rule,
                 **{f"missing_% {y}": miss_year[y] for y in YEARS}, "missing_% pooled": miss,
                 "decision": "candidate" if miss <= MISS_MAX else "excluded (>20% missing)"})
vd = pd.DataFrame(rows)
cands = vd.loc[vd["decision"] == "candidate", "variable"].tolist()
vd.to_csv(RESULTS / "candidate_variables.csv", index=False, encoding="utf-8-sig")
print(vd[["variable", "missing_% pooled", "decision"]].to_string())

ID = ["year", "record", "weight", "weight_pooled", "stratum_u", "psu_u", "plan", "sa_times", "sa"]
pd.concat([a[ID], X[cands]], axis=1).to_csv(DERIVED / "analytic_sample_composites_unimputed.csv",
                                            index=False, encoding="utf-8-sig")
pickle.dump({"vd": vd, "cands": cands}, open(f"{W}/composite_meta.pkl", "wb"))
print(len(a), "adolescents;", len(cands), "candidate predictors (plus suicide plan)")
