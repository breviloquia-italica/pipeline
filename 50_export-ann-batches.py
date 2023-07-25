#!/usr/bin/env python

import modin.pandas as pd
import os

# Load dataset.
wf_fpm_at_doy = pd.read_parquet(
    "wforms-occ.parquet", columns=["tot", "rho", "fst", "lst", "top", "cvx"]
)
ui_fpt_at_doy = pd.read_parquet("wforms-usr.parquet", columns=["tot", "rho"])
wforms = ui_fpt_at_doy.add_prefix("ui_").join(wf_fpm_at_doy.add_prefix("oc_"))
del wf_fpm_at_doy, ui_fpt_at_doy


# NOTE: this must NEVER be changed
wforms["fst_batch"] = (
    (abs(wforms["oc_rho"]) > 0.2) | (abs(wforms["ui_rho"]) > 0.2)
) # & (wforms["oc_tot"] > 5) # NOTE: this excludes a single form, so...

# NOTE: this must NEVER be changed
wforms["snd_batch"] = (
    (wforms["oc_tot"] > 9)  # NOTE: void (accidental)
    & (wforms["ui_tot"] > 9)
    & (~wforms["oc_cvx"].isna())  # NOTE: void (by def. due to next one)
    & ((wforms["oc_lst"] - wforms["oc_fst"]) > 7 * 4)
    & (wforms["oc_fst"] > (0 + 7))
    & (wforms["oc_lst"] > (365 - 14))
)

# Sanity check.
assert wforms.shape[0] == 745121
assert wforms["fst_batch"].sum() == 4296
assert wforms["snd_batch"].sum() == 7906
assert (wforms["fst_batch"] & wforms["snd_batch"]).sum() == 678

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

fst = wforms[wforms["fst_batch"]]
snd = wforms[wforms["snd_batch"] & ~wforms["fst_batch"]]

fst.join(ann, how="left").to_csv("wforms-ann-batch-1.csv", columns=columns)
snd.join(ann, how="left").to_csv("wforms-ann-batch-2.csv", columns=columns)
