#!/bin/bash

sls invoke local -f scraperFeed  -p ./event-data/shopgunSnsFileUpload.json
