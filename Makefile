# TODO: add dependencies from lib

# DATAPREP

# NOTE: this is a proxy for data retrieval, which we don't perform every time ofc.
data: data.zip
	unzip data.zip -d data

places.jsonl: data
	./10_extract-places.sh

tweets.jsonl: data
	./11_extract-tweets.sh

tweets.csv: data
	./12_flatten-tweets.sh

places.parquet: places.jsonl
	./20_cleanup-places.py

tweets.parquet: tweets.jsonl
	./21_cleanup-tweets.py

# NOTE: we skip dependency on external dataset
tweets-tok.parquet: tweets.parquet
	./30_tokenize-tweets.py

tweets-geo.parquet: places.parquet tweets.parquet
	./31_locate-tweets.py

# SELECTION

wforms-occ.parquet: tweets-tok.parquet
	./40_compute-wforms-occ.py

wforms-usr.parquet: tweets-tok.parquet
	./41_compute-wforms-usr.py

wforms-bat.parquet: wforms-occ.parquet wforms-usr.parquet
	./42_compute-wforms-bat.py

# ANNOTATION

# NOTE: there's an optional dependency from wforms-ann.parquet here
wforms-ann-batch-1.csv wforms-ann-batch-2.csv: wforms-bat.parquet
	./50_export-ann-batches.py

51_process-ann-batches.md: tweets.csv wforms-ann-batch-1.csv wforms-ann-batch-2.csv
	touch 51_process-ann-batches.md

# NOTE: we depend on the CSVs since we can't depende on the gsheets
wforms-ann.parquet: wforms-ann-batch-1.csv wforms-ann-batch-2.csv 51_process-ann-batches.md
	./52_import-ann-batches.py

# ANALYSIS

# NOTE: we skip dependency on remote dataset
90_tweets-statistics.ipynb: places.parquet tweets.parquet
	jupyter nbconvert --execute --to notebook --inplace 90_tweets-statistics.ipynb

# NOTE: we skip dependency on remote dataset
92_annos-statistics.ipynb: tweets-geo.parquet tweets-tok.parquet wforms-ann.parquet
	jupyter nbconvert --execute --to notebook --inplace 92_annos-statistics.ipynb