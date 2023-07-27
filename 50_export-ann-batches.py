#!/usr/bin/env python

import modin.pandas as pd
import os

# Load dataset.
wforms = pd.read_parquet("wforms-bat.parquet", columns=["tt_att", "fst_batch", "snd_batch"])

columns = ["status", "category", "attestation", "notes"]

# Import (or generate blank) annotations.
if os.path.exists("wforms-ann.parquet"):
    ann = pd.read_parquet("wforms-ann.parquet", columns=columns)
else:
    ann = pd.DataFrame(
        {
            "wf": pd.Series(dtype=str),
            "status": pd.Series(dtype=float),
            "category": pd.Series(dtype=str),
            "attestation": pd.Series(dtype=str),
            "notes": pd.Series(dtype=str),
        }
    ).set_index("wf")

# Modin dislikes joining empty dataframes, so we add a placecholder (which is ok since we're left joining it away).
ann.loc[".keep"] = None

# NOTE: we keep forms attested in TreeTagger out of the loop.
fst = wforms[~wforms["tt_att"] & wforms["fst_batch"]]
snd = wforms[~wforms["tt_att"] & wforms["snd_batch"] & ~wforms["fst_batch"]]

fst.join(ann, how="left").to_csv("wforms-ann-batch-1.csv", columns=columns)
snd.join(ann, how="left").to_csv("wforms-ann-batch-2.csv", columns=columns)
