#!/bin/bash

yarn --prod=false
yarn build
mkdir .temp || true
yarn --prod --modules-folder .temp/node_modules
rm artifact.zip || true
cd .temp
zip -rq ../artifact.zip node_modules # recursive, quiet
cd ..
zip -rq artifact.zip dist .env.example # recursive, quiet
yarn sls deploy
