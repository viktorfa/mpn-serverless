#!/bin/bash
set -euo pipefail

STAGE=${1:-dev}
echo "Deploying to stage: $STAGE"

# Resolve git short hash or fallback
if GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null); then
  export GIT_COMMIT
else
  export GIT_COMMIT=unknown
fi
echo "Using git commit: $GIT_COMMIT"

./install-layers.sh

./package.sh

pnpm sls deploy --stage $STAGE