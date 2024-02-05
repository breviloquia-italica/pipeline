#!/usr/bin/env python

from datetime import datetime
import modin.pandas as pd
from shapely import wkt
from shapely.geometry import Point

tweets = pd.read_json("tweets.jsonl", lines=True)
tweets = tweets[["id", "created_at", "coordinates", "user_id"]]
tweets.set_index("id", inplace=True)

forms = set(
    pd.read_parquet(
        "wforms-ann.parquet",
        columns=[],
        filters=[
            [
                ("status", ">=", 0)
            ]  # NOTE: this implies ( fst_batch | snd_batch ) & !tt_att
        ],
    ).index
)

tweets_toks = pd.read_parquet("tweets-tok.parquet", columns=["tokens"])
tweets_toks["tokens"] = tweets_toks["tokens"].apply(
    lambda ts: [t for t in ts if t in forms]
)
tweets_toks = tweets_toks[tweets_toks["tokens"].map(bool)]

tweets = tweets.join(tweets_toks, how="right")

tweets_geo = pd.read_parquet(
    "tweets-geo.parquet", columns=["centroid"], filters=[[("id", "in", tweets.index)]]
)

tweets = tweets.join(tweets_geo, how="left")

tweets["coordinates"] = tweets["coordinates"].apply(
    lambda o: None if o is None else Point(o["coordinates"])
)
tweets["coordinates"] = tweets["coordinates"].fillna(tweets["centroid"].map(wkt.loads))

assert 477 == tweets["coordinates"].isna().sum()  # sigh
tweets = tweets[~tweets["coordinates"].isna()]
tweets["latitude"] = tweets["coordinates"].apply(lambda p: p.y)
tweets["longitude"] = tweets["coordinates"].apply(lambda p: p.x)

import uuid

UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "twitter.com")

anonymized = {}


def anonymize(input):
    if pd.isnull(input):
        return input
    return anonymized.setdefault(input, str(uuid.uuid5(UUID_NAMESPACE, str(input))))


assert tweets["user_id"].dtype == "int64"
tweets["user_id"] = tweets["user_id"].apply(anonymize)

tweets["created_at"] = tweets["created_at"].map(lambda dt: dt.isoformat())

tweets.reset_index(inplace=True)

tweets = tweets.explode("tokens")
tweets.rename(
    columns={"created_at": "timestamp", "tokens": "word", "id": "tweet_id"},
    inplace=True,
)
tweets = tweets[["timestamp", "user_id", "tweet_id", "latitude", "longitude", "word"]]

tweets.to_csv("occurrences.csv", index=False)
