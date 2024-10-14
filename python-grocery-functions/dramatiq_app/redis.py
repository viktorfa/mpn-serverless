import os
import dramatiq
from dramatiq.brokers.redis import RedisBroker

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
DRAMATIQ_NAMESPACE = os.environ["DRAMATIQ_NAMESPACE"]


def setup_redis_broker():
    redis_broker = RedisBroker(
        host=REDIS_HOST,
        port=6379,
        namespace=DRAMATIQ_NAMESPACE,
        password=REDIS_PASSWORD,
    )
    dramatiq.set_broker(redis_broker)


def ensure_broker_initialized():
    broker: RedisBroker = dramatiq.get_broker()

    if not broker.namespace == DRAMATIQ_NAMESPACE:
        setup_redis_broker()
        broker = dramatiq.get_broker()
        broker.client.ping()
        return
