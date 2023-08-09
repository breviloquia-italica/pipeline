#=[ Pipeline ]==========================

#-[ External data sources ]-------------

data.zip:
	@echo "You must provide $@ yourself."
	@exit 1

attested-forms.csv:
	@echo "You must provide $@ yourself."
	@exit 1

world-nations.geojson:
	curl -o $@ "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/natural-earth-countries-1_110m@public/exports/geojson?lang=en&timezone=Europe%2FBerlin"

italy-regions.geojson:
	curl -o $@ "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"

#-[ Preparation ]-----------------------

data: data.zip
	./00_unpack-data.sh

places.jsonl: data
	./10_extract-places.sh

places.parquet: places.jsonl
	./20_cleanup-places.py

tweets.jsonl: data
	./11_extract-tweets.sh

tweets.parquet: tweets.jsonl lib/entities.py
	./21_cleanup-tweets.py

tweets.csv: data
	./12_flatten-tweets.sh

preparation: data places.jsonl places.parquet tweets.jsonl tweets.parquet tweets.csv

#-[ Transformation ]--------------------

tweets-geo.parquet: places.parquet tweets.parquet italy-regions.geojson
	./31_locate-tweets.py

tweets-tok.parquet: tweets.parquet lib/tokenizer.py
	./30_tokenize-tweets.py

transformation: tweets-tok.parquet tweets-geo.parquet

#-[ Selection ]-------------------------

wforms-occ.parquet: tweets-tok.parquet
	./40_compute-wforms-occ.py

wforms-usr.parquet: tweets-tok.parquet
	./41_compute-wforms-usr.py

wforms-bat.parquet: wforms-occ.parquet wforms-usr.parquet attested-forms.csv
	./42_compute-wforms-bat.py

selection: wforms-occ.parquet wforms-usr.parquet wforms-bat.parquet

#-[ Annotation ]------------------------

# NOTE: there's an optional dependency from wforms-ann.parquet here.
wforms-ann-batch-1.csv wforms-ann-batch-2.csv: wforms-bat.parquet
	./50_export-ann-batches.py

# NOTE: this is a proxy for an external manual process.
51_process-ann-batches.md: tweets.csv wforms-ann-batch-1.csv wforms-ann-batch-2.csv
	touch 51_process-ann-batches.md

wforms-ann.parquet: 51_process-ann-batches.md
	./52_import-ann-batches.py

#-[ Analysis ]--------------------------

# NOTE: these two prereqs trigger everything else.
9%-statistics.ipynb: tweets-geo.parquet wforms-ann.parquet world-nations.geojson italy-regions.geojson
	jupyter nbconvert --execute --to notebook --inplace $@

analysis: 9*-statistics.ipynb
