#!/usr/bin/env python

import modin.pandas as pd
from scipy.stats import spearmanr

# Load dataset.
tweets = pd.read_parquet("tokens.parquet", columns=["doy", "wforms_new"])
tweets = tweets.join(pd.read_parquet("tweets.parquet", columns=["user_id"]))

# Compute dataframe with exploded prefiltered forms.
wforms = tweets[tweets["wforms_new"].apply(len) > 0]
wforms = wforms.explode("wforms_new")
wforms.rename(columns={"wforms_new": "wf"}, inplace=True)

# Compute daily and total counts.
ui_count_per_doy = tweets.groupby('doy')['user_id'].nunique()
ui_count = wforms.groupby("wf")['user_id'].nunique()

# Compute renormalized pivot table with daily user count (per thousand).
ui_fpt_at_doy = pd.DataFrame(
    wforms.groupby(["doy", "wf"])
    ['user_id'].nunique()
    .multiply(1000)
    .div(ui_count_per_doy, level="doy")
    .reset_index(name="fpt")
    ._to_pandas()  # NOTE: modin chokes on ambiguous indices when pivoting
    .pivot_table(index="wf", columns="doy", values="fpt", fill_value=0)
)

# TODO: compute our heuristics here too?

# Calculate spearman rank correlation (requires int column index).
ui_fpt_at_doy.columns = ui_fpt_at_doy.columns.astype(int)
ui_spearman = ui_fpt_at_doy.apply(lambda row: spearmanr(row.index, row)[0], axis=1)

# Join it all together.
ui_spearman.name = "rho"
ui_count.name = "tot"
ui_fpt_at_doy = ui_fpt_at_doy.join(ui_spearman).join(ui_count)

# Save dataset.
ui_fpt_at_doy.columns = ui_fpt_at_doy.columns.astype(str)
ui_fpt_at_doy.to_parquet("wforms-usr.parquet")
