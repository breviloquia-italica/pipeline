#!/usr/bin/env python

import modin.pandas as pd
import numpy as np
import requests
from io import StringIO

gsheet_csv_export_url_template="https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

def read_annotations_gsheet(sheet_id):
  url = gsheet_csv_export_url_template.format(sheet_id=sheet_id)
  # NOTE: it's crucial to be explicit decoding the request body!
  stream = StringIO(requests.get(url).content.decode('utf-8'))
  return pd.read_csv(
    # read the stream with care for encoding
    stream, encoding='UTF-8',
    # read just the first three columns: word form, status and notes
    usecols=[0, 1], #dtype={0: 'str', 1: 'float', 2: 'str'},
  )


# Fetch first batch.
fst_batch_annotations_gsheet_id="1MCzAM0QRlW6symBUQrlxgVgsaxfJVxf_zlwNu_1gGW8"
fst_batch_annotations = read_annotations_gsheet(fst_batch_annotations_gsheet_id)

# The first annotation batch was prepared with a buggy tokenizer; this partially compensates.
fst_batch_annotations['wf'] = fst_batch_annotations['wf'].str.rstrip("\ue001")
fst_batch_annotations["status"] = fst_batch_annotations["status"].fillna(-np.inf)
fst_batch_annotations = fst_batch_annotations.loc[fst_batch_annotations.groupby('wf')['status'].idxmax()]
fst_batch_annotations["status"] = fst_batch_annotations["status"].replace(-np.inf, np.nan)

# Fetch second batch.
snd_batch_annotations_gsheet_id="1PckY4B9B1jKjsfbIBr2_XwkkcN85UzYQ7cf-vUNQVxo"
snd_batch_annotations = read_annotations_gsheet(snd_batch_annotations_gsheet_id)

# Fetch third batch.
trd_batch_annotations_gsheet_id="1hNi23F1BbB-dUvKwlrzcLvP_17XVdTp1lW8tHmVqunY"
trd_batch_annotations = read_annotations_gsheet(trd_batch_annotations_gsheet_id)

# Check and set indices.
assert ~fst_batch_annotations["wf"].duplicated().any()
assert ~snd_batch_annotations["wf"].duplicated().any()
assert ~trd_batch_annotations["wf"].duplicated().any()
fst_batch_annotations.set_index("wf", inplace=True)
snd_batch_annotations.set_index("wf", inplace=True)
trd_batch_annotations.set_index("wf", inplace=True)

# Check overlaps and concat.
assert fst_batch_annotations.index.intersection(snd_batch_annotations.index).empty
assert snd_batch_annotations.index.intersection(trd_batch_annotations.index).empty
assert trd_batch_annotations.index.intersection(fst_batch_annotations.index).empty
annotations = pd.concat([fst_batch_annotations, snd_batch_annotations, trd_batch_annotations])

# Save dataset.
annotations.to_parquet("wforms-ann.parquet")

