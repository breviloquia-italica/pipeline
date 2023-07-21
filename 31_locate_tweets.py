#!/usr/bin/env python

import modin.pandas as pd
import geopandas as gpd
import pandas as pd
import shapely

# Load Italian regions geometry dataset.
regions = gpd.read_file(
    filename=r"https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"
)

places = pd.read_parquet(
    "places.parquet", columns=["place_type", "country_code", "centroid"]
)
places["centroid"] = places["centroid"].apply(shapely.wkt.loads)

foreign_places = places[(places["country_code"] != "IT")]
italian_nation = places[
    (places["country_code"] == "IT") & (places["place_type"] == "country")
]
italian_places = places[
    (places["country_code"] == "IT") & (places["place_type"] != "country")
]

# EPSG:4326 is WGS 84 geographic coordinate reference system for lat/lon coordinates.
# EPSG:32632 is UTM 32N projected coordinate reference system for UTM coordinates in zone 32, which covers Italy.
italian_places = (
    gpd.sjoin_nearest(
        gpd.GeoDataFrame(italian_places, geometry="centroid", crs="EPSG:4326").to_crs(
            "EPSG:32632"
        ),
        regions.to_crs("EPSG:32632"),
        how="left",
    )
    .to_crs("EPSG:4326")
    .drop(columns=["index_right", "reg_name", "reg_istat_code_num"])
)

places = pd.concat([foreign_places, italian_nation, italian_places])


tweets = pd.read_parquet("tweets.parquet", columns=["place_id", "point"])
# tweets["point"] = tweets["point"].apply(shapely.wkt.loads)

# We have three situations:
tweets_w_place = tweets[tweets["place_id"] != 0]
tweets_w_point = tweets[(tweets["place_id"] == 0) & ~tweets["point"].isna()]
tweets_wo_info = tweets[(tweets["place_id"] == 0) & tweets["point"].isna()]

# The bulk is easily joined to the place.
assert tweets_w_place.shape[0] == 5289905
tweets_w_place = tweets_w_place.join(places, on="place_id")
tweets_w_place = gpd.GeoDataFrame(tweets_w_place, geometry="centroid").to_wkt()

# A map shows the ones near Italy w/o place and w/ point are few and offshore.
# We could try to pinpoint them, but it's not worth the effort.
assert tweets_w_point.shape[0] == 1879

# For the ones w/o any geographical data there's not much to do.
assert tweets_wo_info.shape[0] == 28015

tweets = pd.concat([tweets_w_place, tweets_w_point, tweets_wo_info]).drop(
    columns=["point", "place_type", "place_id"]
)

# NOTE: remember to treat with care the ones generically attributed to "Italy"
assert 3499 == ((tweets["country_code"] == "IT") & tweets["reg_istat_code"].isna()).sum()

# Save dataset.
tweets.to_parquet("tweets-geo.parquet")
