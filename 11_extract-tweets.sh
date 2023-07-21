#!/usr/bin/env bash

JQ_FILTER=".[] | {id,created_at,user_id,full_text,entities,geo,coordinates,place_id:.place.id}"

ls data/*.jsonl | parallel --progress "jq -c -s '$JQ_FILTER' {}" > tweets.jsonl
