#!/bin/bash

# Get the stage (e.g., dev or prod) from the first argument
STAGE=$1

if [ -z "$STAGE" ]; then
  echo "Usage: $0 <stage>"
  echo "Example: $0 dev"
  exit 1
fi

# Set the app folder name dynamically based on the stage
APP_FOLDER="dramatiq_app_mpn_${STAGE}"

# Get git short commit hash for tagging
GIT_HASH=$(git rev-parse --short HEAD)
IMAGE_TAG="registry.vikfand.com/dramatiq-app-mpn:${GIT_HASH}"

# Load environment variables based on the stage
if [ "$STAGE" == "dev" ]; then
  ENV_FILE=".env.dev"
elif [ "$STAGE" == "prod" ]; then
  ENV_FILE=".env.prod"
else
  echo "Invalid stage specified. Please use 'dev' or 'prod'."
  exit 1
fi


# Export the image tag as environment variable for docker-compose
export DRAMATIQ_IMAGE_TAG="${IMAGE_TAG}"

# Convert docker-compose.yml to canonical form to insert env variables
docker compose --env-file ./dramatiq_app/${ENV_FILE} -f ./dramatiq_app/docker-compose-${STAGE}.yml config --no-path-resolution | grep -v '^name' > ./dramatiq_app/docker-compose-${STAGE}.canonical.yml

# Build and push the Docker image
uv export --format requirements-txt --group dramatiq --no-dev > requirements-dramatiq.txt
echo "Building and pushing Docker image: ${IMAGE_TAG}"
docker -D buildx build --build-arg GIT_COMMIT=$GIT_HASH --push --progress=plain -t "${IMAGE_TAG}" -f Dockerfile.dramatiq .

# Sync the files to the remote server using rsync
rsync -avz --delete ./dramatiq_app/ "root@116.203.157.166:/root/${APP_FOLDER}/"

# Log in to the remote server and deploy the stack using docker
ssh root@116.203.157.166 << EOF
  # Navigate to the folder where the docker-compose.canonical.yml is located
  cd "/root/${APP_FOLDER}/"

  # Deploy the stack using docker stack deploy --resolve-image always
  docker stack deploy -c docker-compose-${STAGE}.canonical.yml dramatiq-stack-mpn-${STAGE} --resolve-image always --detach --with-registry-auth
EOF
