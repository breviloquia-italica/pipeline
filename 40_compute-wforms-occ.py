#!/usr/bin/env python

import modin.pandas as pd
from scipy.stats import spearmanr

# Load dataset.
tweets = pd.read_parquet("tokens.parquet", columns=["doy", "wforms_new", "wforms_count"])

# Compute dataframe with exploded prefiltered forms.
wforms = tweets[tweets["wforms_new"].apply(len) > 0]
wforms = wforms.explode("wforms_new")
wforms.rename(columns={"wforms_new": "wf"}, inplace=True)

# Compute daily and total counts.
wf_count_per_doy = tweets.groupby("doy")["wforms_count"].sum()
wf_count = wforms["wf"].value_counts()

# Compute renormalized pivot table with daily form frequency (per million).
wf_fpm_at_doy = pd.DataFrame(
    wforms.groupby(["doy", "wf"])
    .size()
    .multiply(1000000)
    .div(wf_count_per_doy, level="doy")
    .reset_index(name="fpm")
    ._to_pandas()  # NOTE: modin chokes on ambiguous indices when pivoting
    .pivot_table(index="wf", columns="doy", values="fpm", fill_value=0)
)

# NOTE: If you need to compute wf_heuristic on a memory-bound system, just apply
# compute_heuristic to wf_fpm_at_doy. Up to rounding error, it's equivalent.
#
#   def compute_heuristic(row):
#       cs = np.cumsum(row)
#       bot = 0                    # zero
#       top = cs.loc[365]          # maximum (last element due to monotonicity)
#       beg = np.argmax(cs != bot) # first nonzero element (first occurrence)
#       end = np.argmax(cs == top) # first maximum element (last occurrence)
#       # simplified calculation for the normalized residue
#       res = cs[beg:end].sum() # * 2 / top / (end-beg) - 1 # NOTE: normalization can be done later WLOG
#       return pd.Series([beg, end, top, res])
#

wf_fpm_at_doy.columns = wf_fpm_at_doy.columns.astype(str)
cs = wf_fpm_at_doy.cumsum(axis=1) # requires str column index
beg = cs.iloc[:, ::-1].idxmin(axis=1).astype(int)
end = cs.iloc[:, ::+1].idxmax(axis=1).astype(int) - 1
top = cs.max(axis=1)
res = cs.sum(axis=1) - (365 - end) * top # TODO: normalize residue
wf_heuristic = pd.concat({ "beg": beg, "end": end, "top": top, "res": res }, axis=1)
del cs, beg, end, top, res # just to clarify this is intermediate stuff

# Calculate spearman rank correlation (requires int column index).
wf_fpm_at_doy.columns = wf_fpm_at_doy.columns.astype(int)
wf_spearman = wf_fpm_at_doy.apply(lambda row: spearmanr(row.index, row)[0], axis=1)

# Join it all together.
wf_spearman.name = "rho"
wf_count.name = "tot"
wf_fpm_at_doy = wf_fpm_at_doy.join(wf_heuristic).join(wf_spearman).join(wf_count)

# Save dataset.
wf_fpm_at_doy.columns = wf_fpm_at_doy.columns.astype(str)
wf_fpm_at_doy.to_parquet("wforms-occ.parquet")
