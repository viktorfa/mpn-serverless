#!/bin/bash

PYTHON_VERSION=3.11

pdm export --prod > requirements.txt

rm -rf ./layer/common
mkdir -p ./layer/common/python/lib/python$PYTHON_VERSION/site-packages
CFLAGS="-Os -g0" pip install -r ./requirements.txt -t ./layer/common/python/lib/python$PYTHON_VERSION/site-packages --no-cache-dir

echo "Before removing unnecessary files"
du -sh ./layer/common | awk '{print $1}'

find ./layer/common \( \
    -name 'tests' -o \
    -name 'test' -o \
    -name '__pycache__' -o \
    -name '*.pyc' -o \
    -name '*.pyo' -o \
    -name '*.pyd' -o \
    -name '*.pdf' -o \
    -name '*.txt' -o \
    -name 'README*' -o \
    -name 'LICENSE*' -o \
    -name '*.md' -o \
    -name 'examples' -o \
    -name 'docs' \
    \) -exec rm -rf {} +

find "./layer/common" -name "*.so" | xargs strip

echo "After removing unnecessary files"
du -sh ./layer/common | awk '{print $1}'

echo "Layer created successfully!"