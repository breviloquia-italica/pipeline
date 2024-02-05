#!/usr/bin/env bash

JQ_FILTER=".[].id"

ls data/*.jsonl | parallel --progress "jq -c -s '$JQ_FILTER' {}" | sort -u > tweets-ids.csv
