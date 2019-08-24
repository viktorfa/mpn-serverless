#!/bin/bash

yarn --production
serverless deploy --aws-profile serverless-grocery-admin
