#!/bin/sh

export STASH_GRAPHQL="http://127.0.0.1:9999/graphql"
export STASH_API_KEY="<api key>"
export STASH_TAGME_ID="<tagme tag id>"
export STASH_HAS_BEEN_TAGGED_ID="<tagged tag id>"
export STASH_TAG_GENERATED_ID="<tag generated id>"
export STASH_FORMAT_UNSUPPORTED_ID="<format unsupported tag id>"

export DEEPDANBOORU_MODEL_PATH="<model path>"

python tag_images.py