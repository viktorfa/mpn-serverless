#!/bin/bash

sls invoke -f scraperFeedTrigger -d '{"key": "coop/coop_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "kolonial/simple_kolonial_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "meny_api_spider/meny_api_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "europris/europris_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "www.holdbart.no/holdbart_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "shopgun/shopgun_catalog_spider-latest.json"}' -s prod  
sls invoke -f scraperFeedTrigger -d '{"key": "maxsnus.no/maxsnus_spider-latest.json"}' -s prod  
