#!/bin/bash
set -euo pipefail
PYTHON_VERSION=3.11
uv export --no-dev --no-group dramatiq --no-editable --no-hashes --format requirements-txt > ./requirements-lambda.txt
rm -rf ./layer/common && mkdir -p ./layer/common
uv pip install --no-installer-metadata --no-compile-bytecode --python-platform x86_64-manylinux2014 --python $PYTHON_VERSION --prefix ./layer/common/python -r ./requirements-lambda.txt
echo "Before removing unnecessary files"; du -sh ./layer/common | awk '{print $1}'
find ./layer/common \( -name 'tests' -o -name 'test' -o -name '__pycache__' -o -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' -o -name '*.pdf' -o -name '*.txt' -o -name 'README*' -o -name 'LICENSE*' -o -name '*.md' -o -name 'examples' -o -name 'docs' \) -exec rm -rf {} +
find ./layer/common -type f -name "*.so" -print0 | xargs -0 -r strip || true
echo "After removing unnecessary files"; du -sh ./layer/common | awk '{print $1}'
echo "Layer created successfully!"
