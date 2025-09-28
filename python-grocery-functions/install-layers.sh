#!/bin/bash
set -euo pipefail
PYTHON_VERSION=3.12
uv export --no-dev --no-group dramatiq --no-editable --no-hashes --format requirements-txt > ./requirements-lambda.txt
rm -rf ./layer/common && mkdir -p ./layer/common

uv pip install --no-compile-bytecode --python-platform x86_64-manylinux2014 --python "$PYTHON_VERSION" --prefix ./layer/common/python opentelemetry-distro opentelemetry-instrumentation-aws-lambda opentelemetry-exporter-otlp-proto-http -r ./requirements-lambda.txt

mkdir -p ./layer/common/bin
printf '#!/bin/sh\nexec /var/lang/bin/python%s /opt/python/bin/opentelemetry-instrument "$@"\n' "$PYTHON_VERSION" > ./layer/common/bin/otel-wrapper && chmod +x ./layer/common/bin/otel-wrapper
ln -sf opentelemetry-instrument ./layer/common/bin/otel-instrument
[ -f ./layer/common/python/bin/opentelemetry-instrument ] && perl -pi -e 's/\r$//' ./layer/common/python/bin/opentelemetry-instrument

echo "Before removing unnecessary files"; du -sh ./layer/common | awk '{print $1}'
find ./layer/common \( -name tests -o -name test -o -name __tests__ -o -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' -o -name '*.pdf' -o -name 'README*' -o -name 'LICENSE*' -o -name '*.md' -o -name examples -o -name docs \) -exec rm -rf {} + 2>/dev/null || true
find ./layer/common -type f -name "*.so" -print0 | xargs -0 -r strip || true
echo "After removing unnecessary files"; du -sh ./layer/common | awk '{print $1}'
echo "Layer created successfully!"


