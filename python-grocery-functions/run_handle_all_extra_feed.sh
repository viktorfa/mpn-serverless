#!/bin/bash

#sls invoke -f scraperFeedTrigger -d '{"key": "bakeren_feed/bakeren_feed_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "kitchentime_feed/kitchentime_feed_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "cg_feed/cg_feed_spider-latest.json"}' -s prod
sls invoke -f scraperFeedTrigger -d '{"key": "cdon_aggregated_feed/cdon_aggregated_feed_spider-latest.json"}' -s prod


