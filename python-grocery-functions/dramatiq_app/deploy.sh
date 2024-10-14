#!/bin/bash

# Get the stage (e.g., dev or prod) from the first argument
STAGE=$1

# Set the app folder name dynamically based on the stage
APP_FOLDER="dramatiq_app_mpn_${STAGE}"

# Load environment variables based on the stage
if [ "$STAGE" == "dev" ]; then
  ENV_FILE=".env.dev"
elif [ "$STAGE" == "prod" ]; then
  ENV_FILE=".env.prod"
else
  echo "Invalid stage specified. Please use 'dev' or 'prod'."
  exit 1
fi

# Export environment variables from the env file
#export $(grep -v '^#' $ENV_FILE | xargs)

# Convert docker-compose.yml to canonical form to insert env variables
docker compose --env-file ./dramatiq_app/${ENV_FILE} -f ./dramatiq_app/docker-compose-${STAGE}.yml convert --no-path-resolution | grep -v '^name' > ./dramatiq_app/docker-compose-${STAGE}.canonical.yml



# Build and push the Docker image
pdm export > requirements.txt
docker build --file Dockerfile.dramatiq -t ewr.vultrcr.com/vikfandvultryregistry/dramatiq-app-mpn:latest .
docker push ewr.vultrcr.com/vikfandvultryregistry/dramatiq-app-mpn:latest

# Replace quoted integers in the `published` port with unquoted integers
sed -i 's/published: "\(.*\)"/published: \1/' ./dramatiq_app/docker-compose-${STAGE}.canonical.yml

# Sync the files to the remote server using rsync
rsync -avz --delete ./dramatiq_app/ "root@116.203.157.166:/root/${APP_FOLDER}/"

# Log in to the remote server and deploy the stack using docker
ssh root@116.203.157.166 << EOF
  # Navigate to the folder where the docker-compose.canonical.yml is located
  cd "/root/${APP_FOLDER}/"

  # Deploy the stack using docker stack deploy --resolve-image always
  docker stack deploy -c docker-compose-${STAGE}.canonical.yml dramatiq-stack-mpn-${STAGE} --resolve-image always --detach --with-registry-auth
EOF
