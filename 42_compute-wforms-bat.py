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

# Load old attested forms dataset and check presence.
attested_forms = set(pd.read_csv("attested-forms.csv", header=None)[0].str.lower())
attested_forms |= {"#" + f for f in attested_forms}
wforms["tt_att"] = wforms.index.isin(attested_forms)

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
assert wforms.shape[0] == 925843
assert wforms["fst_batch"].sum() == 6737
assert wforms["snd_batch"].sum() == 21132
assert (wforms["fst_batch"] & wforms["snd_batch"]).sum() == 979
assert (~wforms["tt_att"]).sum() == 745121
assert (~wforms["tt_att"] & wforms["fst_batch"]).sum() == 4296
assert (~wforms["tt_att"] & wforms["snd_batch"]).sum() == 7906
assert (~wforms["tt_att"] & wforms["fst_batch"] & wforms["snd_batch"]).sum() == 678

# Save dataset.
wforms[["tt_att", "fst_batch", "snd_batch"]].to_parquet("wforms-bat.parquet")