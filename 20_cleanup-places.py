#!/usr/bin/env python

import modin.pandas as pd
from shapely.geometry import Polygon
import geopandas as gpd

# Load dataset.
places = pd.read_json("places.jsonl", lines=True)

# Convert 16-digit hex ids to 64 bit uints and reset index.
places["id"] = places["id"].apply(int, base=16).astype("uint64")
places.set_index("id", inplace=True)

# Drop useless columns.
places.drop(columns=["url", "name", "country"], inplace=True)

# Ensure `attributes` and `contained_within` are empty, then drop them.
assert ~(places["attributes"].map(len) > 0).any()
assert ~(places["contained_within"].map(len) > 0).any()
places.drop(columns=["attributes", "contained_within"], inplace=True)

# Ensure `bounding_box`, where present, is a polygon with 4 vertices.
assert places["bounding_box"].map(lambda bb: bb["type"] == "Polygon").all()
assert places["bounding_box"].map(lambda bb: len(bb["coordinates"]) == 1).all()
assert (
    places["bounding_box"]
    .map(lambda bb: [len(p) for p in bb["coordinates"][0]] == [2, 2, 2, 2])
    .all()
)

# Simplify the representation of `bounding_box` to the wkt of a Shapely polygon.
places["bounding_box"] = places["bounding_box"].map(
    lambda bb: Polygon([tuple(point) for point in bb["coordinates"][0]])
)

# Calculate centroids of bounding boxes.
places = gpd.GeoDataFrame(places._to_pandas(), geometry="bounding_box")
places["centroid"] = places["bounding_box"].centroid

# Save dataset.
places.to_wkt().to_parquet("places.parquet")
