#!/bin/bash

sls invoke -f scraperFeedTrigger -d '{"key": "lampegiganten_feed/lampegiganten_feed_spider-latest.json"}'  -s prod
