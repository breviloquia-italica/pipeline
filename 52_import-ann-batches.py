#!/usr/bin/env python

import modin.pandas as pd
import numpy as np
import requests
import re
from io import StringIO

def read_annotations_gsheet(sheet_id):
    tpl = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    url = tpl.format(sheet_id=sheet_id)
    # NOTE: it's crucial to be explicit decoding the request body!
    stream = StringIO(requests.get(url).content.decode("utf-8"))
    usecols = ["wf", "status", "category", "attestation", "notes"]
    dtype = { "wf": str, "status": float, "category": str, "attestation": str, "notes": str }
    return pd.read_csv(stream, encoding="UTF-8", usecols=usecols, dtype=dtype)

# First batch: load dataset.
fst = read_annotations_gsheet("1MCzAM0QRlW6symBUQrlxgVgsaxfJVxf_zlwNu_1gGW8")

# First batch: normalize stray entity markers.
if fst["wf"].str.contains(r"[\uE000-\uF8FF]", na=False).any():
    print("First batch: normalizing markers.")
    pfx = re.compile(r"^.*[\uE000\uE010\uE020\uE030\uE040]")
    sfx = re.compile(r"[\uE001\uE011\uE021\uE031\uE041].*$")
    fst["wf"] = fst["wf"].str.replace(pfx, "", regex=True).str.replace(sfx, "", regex=True)
assert ~fst["wf"].str.contains(r"[\uE000-\uF8FF]", na=False).any()

# First batch: normalize duplicates.
if fst["wf"].duplicated().any():
    print("First batch: normalizing duplicates.")
    fst["status"].fillna(-np.inf, inplace=True)
    fst = fst.loc[fst.groupby("wf")["status"].idxmax()]
    fst["status"].replace(-np.inf, np.nan, inplace=True)
assert ~fst["wf"].duplicated().any()

# Second batch: load dataset.
snd = read_annotations_gsheet("1PckY4B9B1jKjsfbIBr2_XwkkcN85UzYQ7cf-vUNQVxo")

# Second batch: normalize stray entity markers.
if snd["wf"].str.contains(r"[\uE000-\uF8FF]", na=False).any():
    print("Second batch: normalizing markers.")
    pfx = re.compile(r"^.*[\uE000\uE010\uE020\uE030\uE040]")
    sfx = re.compile(r"[\uE001\uE011\uE021\uE031\uE041].*$")
    snd["wf"] = snd["wf"].str.replace(pfx, "", regex=True).str.replace(sfx, "", regex=True)
assert ~snd["wf"].str.contains(r"[\uE000-\uF8FF]", na=False).any()

# Second batch: normalize duplicates.
if snd["wf"].duplicated().any():
    print("Second batch: normalizing duplicates.")
    snd["status"].fillna(-np.inf, inplace=True)
    snd = snd.loc[snd.groupby("wf")["status"].idxmax()]
    snd["status"].replace(-np.inf, np.nan, inplace=True)
assert ~snd["wf"].duplicated().any()

# Aggregate annotation batches.
ann = pd.concat([fst,snd], ignore_index=True)

# Aggregate: normalize duplicates.
if ann["wf"].duplicated().any():
    print("Aggregate: normalizing duplicates.")
    ann["status"].fillna(-np.inf, inplace=True)
    ann = ann.loc[ann.groupby("wf")["status"].idxmax()]
    ann["status"].replace(-np.inf, np.nan, inplace=True)
assert ann["wf"].duplicated().sum() == 0

# Aggregate: save dataset.
ann.set_index("wf", inplace=True)

# Save dataset.
ann.to_parquet("wforms-ann.parquet")
