#!/bin/bash

#sls invoke -f scraperFeedTrigger -d '{"key": "se_shopgun_bygg/se_shopgun_bygg_spider-latest.json"}'  -s prod 
sls invoke -f scraperFeedTrigger -d '{"key": "se_byggmax_spider/se_byggmax_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "se_jemogfix_spider/se_jemogfix_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "se_staypro_spider/se_staypro_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "se_beijerbygg_spider/se_beijerbygg_spider-latest.json"}'  -s prod 
#sls invoke -f scraperFeedTrigger -d '{"key": "se_amazon_bygg_spider/se_amazon_bygg_spider-latest.json"}'  -s prod 
