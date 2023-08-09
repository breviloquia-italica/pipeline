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

wforms-ann-batch-1.gsheet.csv:
	curl -o $@ -L "https://docs.google.com/spreadsheets/d/1MCzAM0QRlW6symBUQrlxgVgsaxfJVxf_zlwNu_1gGW8/export?format=csv"

wforms-ann-batch-2.gsheet.csv:
	curl -o $@ -L "https://docs.google.com/spreadsheets/d/1PckY4B9B1jKjsfbIBr2_XwkkcN85UzYQ7cf-vUNQVxo/export?format=csv"

wforms-ann-patches.gsheet.csv:
	curl -o $@ -L "https://docs.google.com/spreadsheets/d/1xOVWZ0Q4NMUANhha97sv_SD25i9A_c1WaAiTPY5dmfo/export?format=csv"

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

preparation: places.parquet tweets.parquet tweets.csv

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

selection: wforms-bat.parquet

#-[ Annotation ]------------------------

wforms-ann-batch-1.csv wforms-ann-batch-2.csv: wforms-bat.parquet
	./50_export-ann-batches.py

51_process-ann-batches.md: tweets.csv wforms-ann-batch-1.csv wforms-ann-batch-2.csv
	@echo "This is a proxy for an external manual process."
	touch 51_process-ann-batches.md

wforms-ann.parquet wforms-ann.csv: 51_process-ann-batches.md wforms-ann-batch-1.gsheet.csv wforms-ann-batch-2.gsheet.csv wforms-ann-patches.gsheet.csv
	./52_import-ann-batches.py

annotation: wforms-ann.parquet wforms-ann.csv

#-[ Analysis ]--------------------------

# NOTE: these two prereqs trigger everything else.
9%-statistics.ipynb: tweets-geo.parquet wforms-ann.parquet world-nations.geojson italy-regions.geojson
	jupyter nbconvert --execute --to notebook --inplace $@

analysis: 9*-statistics.ipynb
