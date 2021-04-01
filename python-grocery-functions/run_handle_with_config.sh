#!/bin/bash

sls invoke -f scraperFeedWithConfigTrigger -d '{"provenance": "cdon_aggregated_feed", "namespace": "cdon", "collection_name": "beautyoffers", "market": "no", "is_partner": true, "categoriesLimits": [], "fieldMapping": [{"source": "image", "destination": "imageUrl", "replace_type": "key"}, {"source": "image_url", "destination": "imageUrl", "replace_type": "key"}, {"source": "url", "destination": "href", "replace_type": "key"}], "extractQuantityFields": [], "ignore_none": false, "feed_key": "cdon_aggregated_feed/cdon_aggregated_feed_spider-latest.json"}' -s dev
