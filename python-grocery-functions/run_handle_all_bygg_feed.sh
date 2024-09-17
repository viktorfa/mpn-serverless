#!/bin/bash

sls invoke -f scraperFeedTrigger -d '{"key": "www.staypro.no/staypro_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "byggmax.no/byggmax_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "vpbygg.no/structured_sitemap_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "gausdal/gausdal_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "obsbygg/obsbygg_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "shopgun_bygg/shopgun_bygg_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "skibygg/skibygg_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "www.maxbo.no/maxbo_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "www.monter.no/monter_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "gront_fokus_feed/gront_fokus_feed_spider-latest.json"}'  -s dev 

sls invoke -f scraperFeedTrigger -d '{"key": "byggern_spider/byggern_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "elektroimportoren_feed/elektroimportoren_feed_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "lampegiganten_feed/lampegiganten_feed_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "jula/jula_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "byggmax_feed/byggmax_feed_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "staypro_feed/staypro_feed_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "flisekompaniet_spider/flisekompaniet_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "megaflis_spider/megaflis_spider-latest.json"}'  -s dev 
sls invoke -f scraperFeedTrigger -d '{"key": "ledlyskilder_feed/ledlyskilder_feed_spider-latest.json"}'  -s dev
sls invoke -f scraperFeedTrigger -d '{"key": "www.jemogfix.no/jemogfix_spider-latest.json"}'  -s dev
