#!/bin/bash

sls invoke -f deleteOffersFromElastic -d '{"engineName": "byggoffers"}'
