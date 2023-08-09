#!/usr/bin/env python

import pandas as pd
import numpy as np

# Read datasets.
dtype = { "wf": str, "status": float, "categories": str, "attestation": str, "notes": str }
usecols = ["wf", "status", "categories", "attestation", "notes"]
fst = pd.read_csv("wforms-ann-batch-1.gsheet.csv", encoding="UTF-8", usecols=usecols, dtype=dtype)
snd = pd.read_csv("wforms-ann-batch-2.gsheet.csv", encoding="UTF-8", usecols=usecols, dtype=dtype)

# Sanity check: no duplicates.
assert ~fst["wf"].duplicated().any()
assert ~snd["wf"].duplicated().any()

# Sanity check: no stray terminators (well, actually two, but we'll drop them during a left join later, whatever).
assert (fst.loc[fst["wf"].str.contains(r"[\uE000-\uF8FF]", na=False),"wf"] == ["more"]).all()
assert (snd.loc[snd["wf"].str.contains(r"[\uE000-\uF8FF]", na=False),"wf"] == [""]).all()

# Aggregate annotation batches.
ann = pd.concat([fst,snd], ignore_index=True)
assert ~ann["wf"].duplicated().any()
ann.set_index("wf", inplace=True)

# Read dataset.
dtype = { "wf": str, "category": str, "categories": str, "attestation": str, "notes": str }
usecols = ["wf", "category", "categories", "attestation", "notes"]
fix = pd.read_csv("wforms-ann-patches.gsheet.csv", encoding="UTF-8", usecols=usecols, dtype=dtype)

# Sanity check: no duplicates, no stray terminators.
assert ~fix["wf"].duplicated().any()
assert 0 == fix["wf"].str.contains(r"[\uE000-\uF8FF]", na=False).sum()

# Sanity check: coherent with annotation batches, all categories are assigned.
assert fix["wf"].isin(ann.index).all()
assert ~fix["category"].isna().any()

# Set index.
fix.set_index("wf", inplace=True)

# Sanity check: no changes on categories, attestation or notes.
assert ann.loc[fix.index, "categories"].equals(fix["categories"])
assert ann.loc[fix.index, "attestation"].equals(fix["attestation"])
assert ann.loc[fix.index, "notes"].equals(fix["notes"])
# Drop them.
fix.drop(columns=["categories", "attestation", "notes"], inplace=True)

# Sanity check: 13 forms were dropped at the last minute.
assert 13 == (~ann[ann["status"].eq(1)].index.isin(fix.index)).sum()

# Apply patches to annotations.
ann.loc[ann["status"].eq(1), "status"] = -1
ann.loc[ann.index.isin(fix.index), "status"] = 1
ann["category"] = np.nan
ann.update(fix)

# Save dataset.
ann.to_parquet("wforms-ann.parquet")
ann.sort_index().to_csv("wforms-ann.csv", encoding="utf-8")
