#!/bin/bash

#sls invoke -f scraperFeedTrigger -d '{"feed_key": "coop/coop_spider-1-latest.json"}' -s dev  
#sls invoke -f scraperFeedTrigger -d '{"feed_key": "europris/europris_spider-latest.json"}' -s dev
sls invoke -f scraperFeedTrigger -d '{"feed_key": "kolonial_spider/kolonial_spider-1-latest.json"}' -s dev  
#sls invoke -f scraperFeedTrigger -d '{"feed_key": "meny_api_spider/meny_api_spider-1-latest.json"}' -s dev  
exit 0
sls invoke -f scraperFeedTrigger -d '{"feed_key": "www.holdbart.no/holdbart_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "shopgun/shopgun_catalog_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "maxsnus.no/maxsnus_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "vivamart_spider/vivamart_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "proteinfabrikken_feed/proteinfabrikken_feed_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "foodstuff_feed/foodstuff_feed_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "slikkepott/slikkepott_spider-latest.json"}' -s dev  
sls invoke -f scraperFeedTrigger -d '{"feed_key": "natur_no_spider/natur_no_spider-latest.json"}' -s dev
exit 0
