#!/usr/bin/env bash

JQ_FILTER=".[].place | select( (. != null) and (.bounding_box != null) )"

ls data/*.jsonl | parallel --progress "jq -c -s '$JQ_FILTER' {} | sort -u" | sort -u  > places.jsonl

