"""Harmonize YRBS 2019-2025 candidate predictors for the ideator sample.
Binary indicators follow CDC QN definitions (1 = condition present, 0 = absent).
Matching is by QN label text because question numbers shift across years."""
import re, pickle
import numpy as np
import pandas as pd

from config import WORK as W, YEARS
meta = pickle.load(open(f"{W}/meta.pkl", "rb"))

def norm(s):
    return re.sub(r"\s+", " ", s.lower().replace("''", "'").replace("\t", " ")).strip()

# name, domain, regular expression matched against the normalized CDC QN variable label
SPEC = [
 ("unsafe_school", "Violence and safety", r"did not go to school because they felt unsafe"),
 ("threatened_weapon_school", "Violence and safety", r"threatened or injured with a weapon on school property"),
 ("fight", "Violence and safety", r"^were in a physical fight$"),
 ("fight_school", "Violence and safety", r"physical fight on school property"),
 ("weapon_school", "Violence and safety", r"carried a weapon on school property"),
 ("gun", "Violence and safety", r"^carried a gun$"),
 ("forced_sex", "Violence and safety", r"physically forced to have sexual intercourse"),
 ("sexual_violence", "Violence and safety", r"^experienced sexual violence$"),
 ("sexual_dating_violence", "Violence and safety", r"experienced sexual dating violence"),
 ("physical_dating_violence", "Violence and safety", r"experienced physical dating violence"),
 ("bullied_school", "Violence and safety", r"bullied on school property"),
 ("ebullied", "Violence and safety", r"electronically bullied"),
 ("sad_hopeless", "Mental health", r"felt sad or hopeless"),
 ("ever_cig", "Tobacco", r"ever tried cigarette smoking|ever smoked a cigarette"),
 ("cig_before13", "Tobacco", r"(first tried cigarette smoking|smoked a cigarette) before age 13"),
 ("current_cig", "Tobacco", r"currently smoked cigarettes"),
 ("cig_10plus", "Tobacco", r"more than 10 cigarettes per day"),
 ("ever_evp", "Tobacco", r"ever used an electronic vapor product"),
 ("current_evp", "Tobacco", r"currently used an electronic vapor product"),
 ("smokeless", "Tobacco", r"currently used smokeless tobacco"),
 ("cigar", "Tobacco", r"currently smoked cigars"),
 ("alc_before13", "Alcohol", r"first drink of alcohol before age 13"),
 ("current_alcohol", "Alcohol", r"currently drank alcohol"),
 ("drinks_10plus", "Alcohol", r"largest number of drinks they had in a row was 10 or more"),
 ("ever_marijuana", "Drugs", r"^ever used marijuana$"),
 ("mj_before13", "Drugs", r"tried marijuana for the first time before age 13"),
 ("current_marijuana", "Drugs", r"currently used marijuana"),
 ("ever_rx_pain_misuse", "Drugs", r"^ever took prescription pain medicine"),
 ("current_rx_pain_misuse", "Drugs", r"currently took prescription pain medicine"),
 ("ever_cocaine", "Drugs", r"ever used cocaine"),
 ("ever_inhalants", "Drugs", r"ever used inhalants"),
 ("ever_heroin", "Drugs", r"ever used heroin"),
 ("ever_meth", "Drugs", r"ever used methamphetamines"),
 ("ever_ecstasy", "Drugs", r"ever used ecstasy"),
 ("ever_inject", "Drugs", r"ever injected any illegal drug"),
 ("ever_hallucinogen", "Drugs", r"ever used hallucinogenic drugs"),
 ("ever_sex", "Sexual behavior", r"^ever had sexual intercourse$"),
 ("sex_before13", "Sexual behavior", r"sexual intercourse for the first time before age 13"),
 ("sex_4plus", "Sexual behavior", r"four or more persons"),
 ("currently_sex_active", "Sexual behavior", r"were currently sexually active"),
 ("perceive_overweight", "Body weight", r"slightly or very overweight"),
 ("trying_lose_weight", "Body weight", r"were trying to lose weight"),
 ("no_fruit", "Diet", r"did not eat fruit"),
 ("no_salad", "Diet", r"did not eat green salad"),
 ("no_potato", "Diet", r"did not eat potatoes"),
 ("no_carrot", "Diet", r"did not eat carrots"),
 ("no_other_veg", "Diet", r"did not eat other vegetables"),
 ("no_soda", "Diet", r"did not drink a can, bottle, or glass of soda"),
 ("no_breakfast", "Diet", r"did not eat breakfast"),
 ("no_sports_drink", "Diet", r"did not drink a can, bottle, or glass of a sports drink"),
 ("no_water", "Diet", r"did not drink a bottle or glass of plain water"),
 ("pa_5days", "Physical activity", r"physically active at least 60 minutes per day on 5 or more days"),
 ("pe_1day", "Physical activity", r"physical education \(pe\) classes on 1 or more days"),
 ("sports_team", "Physical activity", r"played on at least one sports team"),
 ("muscle_3days", "Physical activity", r"strengthen or tone their muscles"),
 ("concussion", "Physical activity", r"had a concussion"),
 ("hiv_test", "Health services", r"tested for human immunodeficiency virus"),
 ("std_test", "Health services", r"tested for a sexually transmitted (disease|infection)"),
 ("dentist", "Health services", r"saw a dentist"),
 ("difficulty_concentrating", "Mental health", r"difficulty concentrating"),
 ("english_well", "Demographics", r"speak english well"),
]

def find_qn(year, pattern):
    hits = [k for k, v in meta[year]["labels"].items() if k.startswith("QN") and re.search(pattern, norm(v))]
    return hits

def find_q(year, labels):
    L = meta[year]["labels"]
    return [k for k, v in L.items() if k.startswith("Q") and not k.startswith("QN") and v.strip() in labels][0]

frames, source = [], {}
for y in YEARS:
    d = pd.read_pickle(f"{W}/yrbs{y}.pkl")
    num = lambda c: pd.to_numeric(d[c], errors="coerce")
    qc = find_q(y, ["Considered suicide"]); qa = find_q(y, ["Attempted suicide", "Actually attempted suicide"])
    qp = find_q(y, ["Made a suicide plan", "Made a suicide plan past 12 months"])
    qh = find_q(y, ["How tall are you"]); qw = find_q(y, ["How much do you weigh"])
    qsl = find_q(y, ["Hours of sleep on school night", "Sleep"]); qsi = find_q(y, ["Sexual identity"])
    out = pd.DataFrame({"year": y, "record": np.arange(1, len(d) + 1), "weight": d["WEIGHT"],
                        "stratum": d["STRATUM"], "psu": d["PSU"]})
    age, grade = num("Q1"), num("Q3")
    si, sa, plan = num(qc), num(qa), num(qp)
    out["age"] = age + 11                       # code 3..6 -> 14..17
    out["grade"] = grade + 8                    # code 1..4 -> 9..12
    out["female"] = (num("Q2") == 1).astype(float).where(num("Q2").notna())
    re_code = pd.to_numeric(d["RACEETH"], errors="coerce")
    if y == 2025:   # 2025 adds Middle Eastern/North African and reorders codes
        rmap = {1: "Other", 2: "Asian", 3: "Black", 4: "Hispanic", 5: "Other", 6: "Other", 7: "White", 8: "Hispanic", 9: "Other"}
    else:
        rmap = {1: "Other", 2: "Asian", 3: "Black", 4: "Other", 5: "White", 6: "Hispanic", 7: "Hispanic", 8: "Other"}
    out["raceeth"] = re_code.map(rmap)
    h, w = num(qh), num(qw)
    out["bmi"] = (w / h ** 2).where(h.notna() & w.notna())
    out["sleep_hours"] = (num(qsl) + 3).where(num(qsl).between(1, 7))   # 1->4h ... 7->10h+
    sid = num(qsi)
    if y == 2019:
        out["sexual_minority"] = sid.map({1: 0, 2: 1, 3: 1, 4: 1})
    else:
        out["sexual_minority"] = sid.map({1: 0, 2: 1, 3: 1, 4: 1, 5: 1})  # 6 = didn't understand -> missing
    src = {}
    out["plan"] = plan.map({1: 1, 2: 0})
    for nm, lab in [("cig_init", "Initiation of cigarette smoking"), ("alc_init", "Initiation of alcohol use"),
                    ("mj_init", "Initiation of marijuana use")]:
        qi = find_q(y, [lab]); out[nm] = num(qi); src[nm] = qi
    out["sa_times"] = sa
    out["sa"] = (sa >= 2).astype(float).where(sa.between(1, 5))
    out["si"] = si.map({1: 1, 2: 0})
    src.update({"si": qc, "sa": qa, "plan": qp, "bmi": f"{qh}/{qw}", "sleep_hours": qsl, "sexual_minority": qsi,
           "age": "Q1", "grade": "Q3", "female": "Q2", "raceeth": "RACEETH"})
    for name, _, pat in SPEC:
        hits = find_qn(y, pat)
        if len(hits) == 1:
            out[name] = num(hits[0]).map({1: 1, 2: 0})
            src[name] = hits[0]
        elif len(hits) == 0:
            out[name] = np.nan; src[name] = None
        else:
            raise ValueError(f"{y} {name} ambiguous {hits}")
    out["eligible"] = age.between(3, 6) & grade.between(1, 4) & (si == 1) & sa.between(1, 5)
    frames.append(out); source[y] = src

full = pd.concat(frames, ignore_index=True)
full["stratum_u"] = full["year"].astype(str) + "_" + full["stratum"].astype("Int64").astype(str)
full["psu_u"] = full["year"].astype(str) + "_" + full["psu"].astype("Int64").astype(str)
ana = full[full["eligible"]].copy()
# pooled weight: within each wave rescale so weights sum to that wave's eligible n
ana["weight_pooled"] = ana.groupby("year")["weight"].transform(lambda w: w * len(w) / w.sum())
ana.to_pickle(f"{W}/analytic_raw.pkl")
pickle.dump({"source": source, "spec": SPEC}, open(f"{W}/harmonize_meta.pkl", "wb"))
print(ana.shape, ana.groupby("year")["sa"].agg(["size", "sum", "mean"]))
print("unmatched:", {y: [k for k, v in s.items() if v is None] for y, s in source.items()})
