#=[ HPC cluster sync ]==================

HPC_USER = pbrasolin@eurac.edu
HPC_HOST = hpc.scientificnet.org
HPC_PATH = /data/users/eurac\\\\pbrasolin/bi/

rsync := rsync -avh --progress --include='**.gitignore' --exclude='/.git' --filter=':- .gitignore'

hpc-pull:
	$(rsync) $(HPC_USER)@$(HPC_HOST):$(HPC_PATH) ./

hpc-push:
	$(rsync) ./ $(HPC_USER)@$(HPC_HOST):$(HPC_PATH)

#=[ Pipeline ]==========================

# TODO: add dependencies from lib

#-[ Preparation ]-----------------------

data: data.zip
	./00_retrieve-data.sh

places.jsonl: data
	./10_extract-places.sh

places.parquet: places.jsonl
	./20_cleanup-places.py

tweets.jsonl: data
	./11_extract-tweets.sh

tweets.parquet: tweets.jsonl
	./21_cleanup-tweets.py

tweets.csv: data
	./12_flatten-tweets.sh

#-[ Transformation ]--------------------

# NOTE: we skip dependency on external geographic datasets.
tweets-geo.parquet: places.parquet tweets.parquet
	./31_locate-tweets.py

tweets-tok.parquet: tweets.parquet
	./30_tokenize-tweets.py

#-[ Selection ]-------------------------

wforms-occ.parquet: tweets-tok.parquet
	./40_compute-wforms-occ.py

wforms-usr.parquet: tweets-tok.parquet
	./41_compute-wforms-usr.py

# NOTE: we skip dependency on external attestation dataset.
wforms-bat.parquet: wforms-occ.parquet wforms-usr.parquet
	./42_compute-wforms-bat.py

# ANNOTATION

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
9%-statistics.ipynb: tweets-geo.parquet wforms-ann.parquet
	jupyter nbconvert --execute --to notebook --inplace $@

analysis: 9*-statistics.ipynb
