#!/bin/bash

sls invoke -f processGroceryOffers -l -d '{"mongoCollection": "figroceryoffers"}' -s dev
