import os
from dotenv import load_dotenv

print("dramatiq_app/app.py started")

# Env variables related to Dramatiq
STAGE = os.environ["STAGE"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
DRAMATIQ_NAMESPACE = f"dramatiq_mpn_{STAGE}"

# Env variables from the rest of the app that is currently AWS Lambdas
load_dotenv(dotenv_path=f".env.{STAGE}")

import dramatiq
from dramatiq.brokers.redis import RedisBroker

# Connect to the Redis instance running on localhost
redis_broker = RedisBroker(
    host=REDIS_HOST,
    port=6379,
    namespace=DRAMATIQ_NAMESPACE,
    password=REDIS_PASSWORD,
)
dramatiq.set_broker(redis_broker)


# Make sure actors are registered in the containerized app
import dramatiq_app.actors

print("dramatiq_app/app.py finished")
