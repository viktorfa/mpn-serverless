#!/bin/bash

sls invoke -f scraperFeedTrigger -d '{"feed_key": "coop/coop_spider-1-latest.json"}' -s prod
sls invoke -f scraperFeedTrigger -d '{"feed_key": "kolonial_spider/kolonial_spider-1-latest.json"}' -s prod
sls invoke -f scraperFeedTrigger -d '{"feed_key": "meny_api_spider/meny_api_spider-1-latest.json"}' -s prod
