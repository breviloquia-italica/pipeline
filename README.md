# breviloquia-italica

```mermaid
flowchart TD;

00[[00_data-retrieval.md]]:::code;
00 --> 2022-MM-DD.jsonl[/2022-MM-DD.jsonl/]:::data;

10[10_extract-places.sh]:::code;
11[11_extract-tweets.sh]:::code;
12[12_flatten-tweets.sh]:::code;
2022-MM-DD.jsonl --- 10 --> places.jsonl[/places.jsonl/]:::data;
2022-MM-DD.jsonl --- 11 --> tweets.jsonl[/tweets.jsonl/]:::data;
2022-MM-DD.jsonl --- 12 --> tweets.csv[/tweets.csv/]:::data;

20[20_cleanup-places.py]:::code;
21[21_cleanup-tweets.py]:::code;
places.jsonl --- 20 --> places.parquet[/places.parquet/]:::data;
tweets.jsonl --- 21 --> tweets.parquet[/tweets.parquet/]:::data;

31[31_locate-tweets.ipynb]:::code;
places.parquet --- 31;
tweets.parquet --- 31 --> tweets-geo.parquet[/tweets-geo.parquet/]:::data;

30[30_tokenize-tweets.ipynb]:::code;
tweets.parquet --- 30;
attested.csv[/attested.csv/]:::data --- 30;
30 --> tokens.parquet[/tokens.parquet/]:::data;

40[40_compute-wforms-occ.ipynb]:::code;
tokens.parquet --- 40 --> wforms-occ.parquet[/wforms-occ.parquet/]:::data;

41[41_compute-wforms-usr.ipynb]:::code;
tokens.parquet --- 41 --> wforms-usr.parquet[/wforms-usr.parquet/]:::data;

50[50_export-ann-batches.py]:::code;
wforms-occ.parquet --- 50;
wforms-usr.parquet --- 50;
50 --> wforms-ann-batch-N.csv[/"wforms-ann-batch-N.csv"/]:::data;

51[[51_process-ann-batches.md]]:::code;
wforms-ann-batch-N.csv --- 51 --> wforms-ann-batch-N.gsheet[/wforms-ann-batch-N.gsheet/]:::data;
wforms-ann.parquet -.-> 50;

52[52_import-annotations.py]:::code;
wforms-ann-batch-N.gsheet --- 52 --> wforms-ann.parquet[/wforms-ann.parquet/]:::data;

60[60_analyze-wforms.ipynb]:::code;
wforms-occ.parquet --- 60;
wforms-ann.parquet --- 60;
wforms-usr.parquet --- 60;
60 --> wforms.parquet[/wforms.parquet/]:::data;

classDef code stroke:red;
classDef data stroke:green,shape:rectangle;
```
