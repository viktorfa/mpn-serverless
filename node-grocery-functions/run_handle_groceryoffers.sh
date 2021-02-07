#!/bin/bash

sls invoke -f processGroceryOffers -l -d '{"mongoCollection": "groceryoffers"}' -s prod
