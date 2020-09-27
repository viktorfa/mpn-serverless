#!/bin/bash

yarn
yarn build
mv node_modules _node_modules
yarn --prod
rm artifact.zip
zip -rq artifact.zip node_modules dist # recursive, quiet
rm -rf node_modules
mv _node_modules node_modules
sls deploy
