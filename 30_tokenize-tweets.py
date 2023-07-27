#!/usr/bin/env python

import modin.pandas as pd
import re
from emoji import replace_emoji
from lib.tokenizer import tokenize_and_filter_wforms

# Load dataset.
tweets = pd.read_parquet("tweets.parquet")

# Strip emojis, normalize whitespace, normalize case, tokenize and extract word forms.
tweets["tokens"] = (
    tweets["text_with_inlined_entities"]
    .apply(replace_emoji, replace=" ")
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    .str.lower()
    .apply(tokenize_and_filter_wforms)
)

# Quantize timestamp as day of year.
tweets["doy"] = tweets["created_at"].dt.dayofyear

# NOTE: remember NOT to deduplicate to avoid undercounting.
# tweets["wforms"] = tweets["wforms"].apply(set)
# tweets["wforms_new"] = tweets["wforms_new"].apply(set)

tweets["token_count"] = tweets["tokens"].apply(len)

# Save dataset.
tweets[["doy", "tokens", "token_count"]].to_parquet("tweets-tok.parquet")
