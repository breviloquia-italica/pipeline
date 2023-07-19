#!/usr/bin/env bash

JQ_FILTER=".[].full_text"

ls data/*.jsonl | parallel --progress "jq -c -s '$JQ_FILTER' {}" > tweets.csv
