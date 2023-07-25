# breviloquia-italica

```mermaid
flowchart TD;

subgraph P1 [PREPARATION]

00[[00_data-retrieval.md]]:::code;
10[10_extract-places.sh]:::code;
11[11_extract-tweets.sh]:::code;
12[12_flatten-tweets.sh]:::code;
20[20_cleanup-places.py]:::code;
21[21_cleanup-tweets.py]:::code;

2022-MM-DD.jsonl[/2022-MM-DD.jsonl/]:::data;
places.jsonl[/places.jsonl/]:::data;
places.parquet[/places.parquet/]:::data;
tweets.jsonl[/tweets.jsonl/]:::data;
tweets.parquet[/tweets.parquet/]:::data;
tweets.csv[/tweets.csv/]:::data;

00 --> 2022-MM-DD.jsonl;

2022-MM-DD.jsonl --- 10 --> places.jsonl;
places.jsonl --- 20 --> places.parquet;

2022-MM-DD.jsonl --- 11 --> tweets.jsonl;
tweets.jsonl --- 21 --> tweets.parquet;

2022-MM-DD.jsonl --- 12 ----> tweets.csv;

end

subgraph P2 [TRANSFORMATION]

30[30_tokenize-tweets.py]:::code;
31[31_locate-tweets.py]:::code;

tokens.parquet[/tokens.parquet/]:::data;
tweets-geo.parquet[/tweets-geo.parquet/]:::data;

_01[/world-nations.geojson/]:::extdata --- 31;
_02[/italy-regions.geojson/]:::extdata ---- 31;
places.parquet ----- 31;
tweets.parquet --- 31;
31 --> tweets-geo.parquet;

tweets.parquet --- 30;
_03[/attested-forms.csv/]:::extdata --- 30;
30 --> tokens.parquet;

end

subgraph P3 [SELECTION]

40[40_compute-wforms-occ.py]:::code;
41[41_compute-wforms-usr.py]:::code;
42[42_compute-wforms-bat.py]:::code;

wforms-occ.parquet[/wforms-occ.parquet/]:::data;
wforms-usr.parquet[/wforms-usr.parquet/]:::data;
wforms-bat.parquet[/wforms-bat.parquet/]:::data;

tokens.parquet --- 40 --> wforms-occ.parquet;

tokens.parquet --- 41;
tweets.parquet --- 41;
41 --> wforms-usr.parquet;

wforms-occ.parquet --- 42;
wforms-usr.parquet --- 42;
42 --> wforms-bat.parquet;

end

subgraph P4 [ANNOTATION]

50[50_export-ann-batches.py]:::code;
51[[51_process-ann-batches.md]]:::code;
52[52_import-ann-batches.py]:::code;

wforms-ann-batch-N.csv[/"wforms-ann-batch-{1,2}.csv"/]:::data
wforms-ann-batch-N.gsheet[/"wforms-ann-batch-{1,2}.gsheet"/]:::extdata;
wforms-ann.parquet[/wforms-ann.parquet/]:::data;

wforms-bat.parquet --- 50;
50 -.- wforms-ann.parquet;
50 --> wforms-ann-batch-N.csv;

wforms-ann-batch-N.csv --- 51;
tweets.csv --- 51;
51 --> wforms-ann-batch-N.gsheet;

wforms-ann-batch-N.gsheet --- 52 --> wforms-ann.parquet;

end

subgraph P5 [ANALYSIS]

direction LR;

90[90_tweets-statistics.ipynb]:::code;
91[91_wforms-statistics.ipynb]:::code;
92[92_annos-statistics.ipynb]:::code;

places.parquet.ref[/places.parquet/]:::dataref;
tweets.parquet.ref[/tweets.parquet/]:::dataref;
tokens.parquet.ref[/tokens.parquet/]:::dataref;
tweets-geo.parquet.ref[/tweets-geo.parquet/]:::dataref;
wforms-bat.parquet.ref[/wforms-bat.parquet/]:::dataref;
wforms-ann.parquet.ref[/wforms-ann.parquet/]:::dataref;

wforms-bat.parquet.ref --- 91;
tokens.parquet.ref --- 91;
tokens.parquet.ref --- 92;
wforms-ann.parquet.ref --- 92;
tweets-geo.parquet.ref --- 92;
_04[/ita-regions.geojson/]:::extdata --- 92;
_04[/ita-regions.geojson/]:::extdata --- 90;
_05[/wld-nations.geojson/]:::extdata --- 90;
places.parquet.ref --- 90;
tweets.parquet.ref --- 90;

90 -.-> 90;
91 -.-> 91;
92 -.-> 92;

end

%%P1 -.- P5;
%%P2 -.- P5;
%%P3 -.- P5;
%%P4 -.- P5;

P1 ~~~~~~~~ P2;
P4 ~~~~~~~~ P5;

classDef code stroke:red;
classDef data stroke:green;
classDef extdata stroke:blue;
classDef dataref stroke:green,stroke-width:2px,stroke-dasharray: 10 10,font-style:italic;
```

---
