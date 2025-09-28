#!/bin/bash


# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
SKIP_CONFIRM=false
APP_NAME=""

# Parse options
while getopts "y" opt; do
  case $opt in
    y)
      SKIP_CONFIRM=true
      ;;
    *)
      ;;
  esac
done

# Shift past the processed options (in this case, -y)
shift $((OPTIND - 1))


APP_NAME=$(<"$SCRIPT_DIR/app_name")

echo -e "The application name is: \e[1m$APP_NAME\e[0m"

# Function to ask for confirmation
confirm() {
  read -r -p "Do you want to continue? (y/N): " response
  case "$response" in
    [yY][eE][sS]|[yY]) 
      true
      ;;
    *)
      false
      ;;
  esac
}

# Ask for confirmation if -y flag is not passed
if [ "$SKIP_CONFIRM" = false ]; then
  if ! confirm; then
    echo "Operation cancelled."
    exit 1
  fi
fi


# Exit if not provided
if [ -z "$APP_NAME" ]; then
  echo "Please provide an app name"
  exit 1
fi


# Get the stage (e.g., dev or prod) from the first argument
STAGE=$1

# Exit if not provided
if [ -z "$STAGE" ]; then
  echo "Please provide a stage"
  exit 1
fi

# Set the app folder name dynamically based on the stage
APP_FOLDER="fastify-$APP_NAME-$STAGE"

DOCKER_IMAGE_NAME="fra.vultrcr.com/crvikfandfrankfurt/mpn-fastify-app:latest"

# Get git commit short hash
GIT_COMMIT=$(git rev-parse --short HEAD)
echo "Building with Git commit: $GIT_COMMIT"

docker build --build-arg GIT_COMMIT=$GIT_COMMIT -f Dockerfile.fastify -t $DOCKER_IMAGE_NAME .
docker push $DOCKER_IMAGE_NAME

# Load environment variables based on the stage
if [ "$STAGE" == "dev" ]; then
  ENV_FILE=".env.dev"
elif [ "$STAGE" == "prod" ]; then
  ENV_FILE=".env.prod"
else
  echo "Invalid stage specified. Please use 'dev' or 'prod'."
  exit 1
fi

# Set OTEL_RESOURCE_ATTRIBUTES with actual values
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=mpn,deployment.environment=${STAGE},service.version=${GIT_COMMIT}"

# Convert docker-compose.yml to canonical form to insert env variables
docker compose --env-file ./${ENV_FILE} -f ./deploy/docker-compose-${STAGE}.yml config --no-path-resolution | grep -v '^name' > ./deploy/docker-compose-${STAGE}.canonical.yml

# Sync the files to the remote server using rsync
rsync -avz --delete ./deploy/ "root@116.203.157.166:/root/${APP_FOLDER}/"


# Log in to the remote server and deploy the stack using docker
ssh root@116.203.157.166 << EOF
  # Navigate to the folder where the docker-compose.yml is located
  cd "/root/${APP_FOLDER}/"

  # Deploy the stack using docker stack deploy
  docker stack deploy -c docker-compose-${STAGE}.canonical.yml fastify-$APP_NAME-$STAGE-stack --resolve-image always --detach --with-registry-auth
EOF
