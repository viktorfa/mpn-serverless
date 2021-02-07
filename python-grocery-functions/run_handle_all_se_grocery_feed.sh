#!/bin/bash

sls invoke -f scraperFeedTrigger -d '{"key": "se_hemkop_spider/se_hemkop_spider-latest.json"}'  -s prod 
sls invoke -f scraperFeedTrigger -d '{"key": "se_mat_se_spider/se_mat_se_spider-latest.json"}'  -s prod 
sls invoke -f scraperFeedTrigger -d '{"key": "se_matsmart_spider/se_matsmart_spider-latest.json"}'  -s prod 
sls invoke -f scraperFeedTrigger -d '{"key": "se_shopgun_grocery/se_shopgun_grocery_spider-latest.json"}'  -s prod 
