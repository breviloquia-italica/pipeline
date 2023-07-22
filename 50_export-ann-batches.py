#!/usr/bin/env python

import modin.pandas as pd

# Load dataset.
wf_fpm_at_doy = pd.read_parquet(
    "wforms-occ.parquet", columns=["tot", "rho", "fst", "lst", "top", "cvx"]
)
ui_fpt_at_doy = pd.read_parquet("wforms-usr.parquet", columns=["tot", "rho"])
wforms = ui_fpt_at_doy.add_prefix("ui_").join(wf_fpm_at_doy.add_prefix("oc_"))
del wf_fpm_at_doy, ui_fpt_at_doy


# NOTE: this must NEVER be changed
wforms["fst_batch"] = (wforms["oc_tot"] > 5) & (
    (abs(wforms["oc_rho"]) > 0.2) | (abs(wforms["ui_rho"]) > 0.2)
)

# NOTE: this must NEVER be changed
wforms["snd_batch"] = (
    (wforms["oc_tot"] > 9)  # NOTE: void (accidental)
    & (wforms["ui_tot"] > 9)
    & (~wforms["oc_cvx"].isna())  # NOTE: void (by def. due to next one)
    & ((wforms["oc_lst"] - wforms["oc_fst"]) > 7 * 4)
    & (wforms["oc_fst"] > (0 + 7))
    & (wforms["oc_lst"] > (365 - 14))
)


# The export we annotated is older than this version of the code.
# These are sanity checks to keep track of the discrepancies.
# There are 6 less forms due to tokenization/serialization changes.
assert wforms.shape[0] == 745127 - 6
# There are 3 more forms due to a fix in forms counting.
assert wforms["fst_batch"].sum() == 4292 + 3
assert wforms["snd_batch"].sum() == 7906
assert (wforms["fst_batch"] & wforms["snd_batch"]).sum() == 678

# Export the first annotation batch.
wforms[wforms["fst_batch"]].to_csv("wforms-ann-batch-1.csv", columns=[])

# Export the second annotation batch.
wforms[wforms["snd_batch"] & ~wforms["fst_batch"]].to_csv(
    "wforms-ann-batch-2.csv", columns=[]
)


# Export the third annotation batch.
trd_batch = wforms[
    (
        (  # this is just fst_batch w/o conditions on oc_tot
            (abs(wforms["oc_rho"]) > 0.2) | (abs(wforms["ui_rho"]) > 0.2)
        )
        | wforms["snd_batch"]
    )
    & ~wforms.index.isin(pd.read_parquet("wforms-ann.parquet").index)
]
# This is a fix for discrepancies and an extension to fst_batch mask, so we need to export it only once.
if trd_batch.empty:
    print("Skipping third batch.")
else:
    trd_batch.to_csv("wforms-ann-batch-3.csv", columns=[])
