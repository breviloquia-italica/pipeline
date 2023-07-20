#!/usr/bin/env python

import modin.pandas as pd
from shapely.geometry import Point
from lib.entities import inline_entities_in_full_text, ENTITY_DELIMITERS_BY_KEY

# Load dataset.
tweets = pd.read_json("tweets.jsonl", lines=True)

# Reset index.
tweets.set_index("id", inplace=True)

# Check assumptions on geographical data.
assert (tweets["geo"].isna() == tweets["coordinates"].isna()).all()
assert tweets["geo"].map(lambda x: x["type"] == "Point", "ignore").all()
assert tweets["coordinates"].map(lambda x: x["type"] == "Point", "ignore").all()
assert tweets["geo"].map(lambda x: len(x["coordinates"]) == 2, "ignore").all()
assert tweets["coordinates"].map(lambda x: len(x["coordinates"]) == 2, "ignore").all()
assert (
    tweets["geo"].dropna().map(lambda x: x["coordinates"]).map(reversed).map(list)
    == tweets["coordinates"].dropna().map(lambda x: x["coordinates"])
).all()

# Normalize geographical data.
tweets["point"] = tweets["coordinates"].map(
    lambda x: Point(x["coordinates"]).wkt, "ignore"
)
tweets.drop(columns=["geo", "coordinates"], inplace=True)
tweets["place_id"] = tweets["place_id"].fillna("0").apply(int, base=16).astype("uint64")

# Check assumptions on textual data.
assert (
    tweets["entities"]
    .map(lambda x: all(k in ENTITY_DELIMITERS_BY_KEY.keys() for k in x.keys()))
    .all()
)

# Normalize textual data.
tweets["text_with_inlined_entities"] = tweets[["full_text", "entities"]].apply(inline_entities_in_full_text, axis=1)
tweets.drop(columns=["full_text", "entities"], inplace=True)

# Save dataset.
tweets.to_parquet("tweets.parquet")
