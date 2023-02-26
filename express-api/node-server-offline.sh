#!/bin/bash

yarn build:js
MPN_NOT_LAMBDA=1 node dist/server
