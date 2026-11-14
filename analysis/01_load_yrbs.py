"""Parse national YRBS ASCII files using CDC SAS input programs.
Outputs per-year parquet-like pickles plus label/format dictionaries."""
import re, sys, json, pickle
import pandas as pd
import numpy as np

from config import RAW, WORK as OUT


def parse_input(sas_path):
    txt = open(sas_path, encoding="latin-1").read()
    specs = []
    for m in re.finditer(r"@(\d+)\s+(\w+)\s+(\$?)(\d+)\.(\d*)", txt):
        start, name, char, width, dec = m.groups()
        specs.append((name, int(start) - 1, int(width), char == "$", int(dec) if dec else 0))
    labels = dict(re.findall(r'^\s*(\w+)\s*=\s*"([^"]*)"', txt, flags=re.M))
    fmt_block = re.search(r"^\s*format\s*$(.*?);", txt, flags=re.S | re.I | re.M)
    fmt_assign = dict(re.findall(r"(\w+)\s+\$?([A-Za-z]\w*)\.", fmt_block.group(1))) if fmt_block else {}
    return specs, labels, fmt_assign


def parse_formats(sas_path):
    txt = open(sas_path, encoding="latin-1").read()
    fmts = {}
    for block in re.finditer(r"value\s+(\$?\w+)(.*?);", txt, flags=re.S | re.I):
        name, body = block.groups()
        pairs = re.findall(r"[\"']([^\"']*)[\"']\s*=\s*[\"']([^\"']*)[\"']", body)
        fmts[name.lstrip("$").upper()] = {k: v for k, v in pairs}
    return fmts


def load_year(y):
    specs, labels, fmt_assign = parse_input(f"{RAW}/{y}XXH-SAS-Input-Program.sas")
    fmts = parse_formats(f"{RAW}/{y}XXH-Formats-Program.sas")
    colspecs = [(s, s + w) for _, s, w, _, _ in specs]
    names = [n for n, *_ in specs]
    df = pd.read_fwf(f"{RAW}/XXH{y}_YRBS_Data.dat", colspecs=colspecs, names=names,
                     dtype=str, header=None, encoding="latin-1")
    for n, s, w, is_char, dec in specs:
        col = df[n].str.strip().replace("", np.nan)
        if is_char:
            df[n] = col
        else:
            num = pd.to_numeric(col, errors="coerce")
            # implied decimals only apply when no explicit decimal point present
            if dec and not col.dropna().str.contains(r"\.").any():
                num = num / (10 ** dec)
            df[n] = num
    df["year"] = y
    return df, labels, fmt_assign, fmts


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for y in [2019, 2021, 2023, 2025]:
        df, labels, fa, fmts = load_year(y)
        df.to_pickle(f"{OUT}/yrbs{y}.pkl")
        meta[y] = {"labels": labels, "fmt_assign": fa, "formats": fmts}
        print(y, df.shape, "weight sum", round(df["WEIGHT"].sum(), 1),
              "Q1 counts", df["Q1"].value_counts(dropna=False).to_dict())
    pickle.dump(meta, open(f"{OUT}/meta.pkl", "wb"))
