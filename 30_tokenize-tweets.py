#!/usr/bin/env python

import modin.pandas as pd
import re
from emoji import replace_emoji
from lib.tokenizer import tokenize_and_filter_wforms

# Load dataset.
tweets = pd.read_parquet("tweets.parquet")

# Strip emojis, normalize whitespace, normalize case, tokenize and extract word forms.
tweets["wforms"] = (
    tweets["text_with_inlined_entities"]
    .apply(replace_emoji, replace=" ")
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    .str.lower()
    .apply(tokenize_and_filter_wforms)
)

# Load old attested forms dataset.
attested_forms = set(pd.read_csv("lessico-TreeTagger.csv", header=None)[0].str.lower())
attested_forms |= {"#" + f for f in attested_forms}

# Prefilter old attested forms.
tweets["wforms_new"] = tweets["wforms"].apply(
    lambda wfs: [wf for wf in wfs if wf not in attested_forms]
)

# Quantize timestamp as day of year.
tweets["doy"] = tweets["created_at"].dt.dayofyear

# TODO: decide whether i fucked up here or not by deduplicating.
tweets["wforms"] = tweets["wforms"].apply(set)
tweets["wforms_new"] = tweets["wforms_new"].apply(set)
tweets["wforms_count"] = tweets["wforms"].apply(len)

# Save dataset.
tweets[["doy", "wforms", "wforms_new", "wforms_count"]].to_parquet("tokens.parquet")
