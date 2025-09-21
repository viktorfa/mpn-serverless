import argparse
import os

import dramatiq
import redis
from dotenv import load_dotenv
from dramatiq.brokers.redis import RedisBroker


class DramatiqQueueHandler:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name

        # Remove Prometheus middleware
        if dramatiq.middleware.default_middleware:
            popped_middleware = dramatiq.middleware.default_middleware.pop(0)
            print(f"Removed middleware: {popped_middleware}")

        # Load environment variables
        REDIS_HOST = os.environ["LAMBDA_REDIS_HOST"]
        REDIS_PORT = int(os.environ.get("LAMBDA_REDIS_PORT", 6379))
        REDIS_DB = int(os.environ.get("LAMBDA_REDIS_DB", 0))
        REDIS_PASSWORD = os.environ["LAMBDA_REDIS_PASSWORD"]
        DRAMATIQ_NAMESPACE = os.environ["DRAMATIQ_NAMESPACE"]

        # Initialize Redis client
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

        # Initialize Dramatiq Redis broker
        self.redis_broker = RedisBroker(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            namespace=DRAMATIQ_NAMESPACE,
            password=REDIS_PASSWORD,
        )
        dramatiq.set_broker(self.redis_broker)

        # Define the queue names you're using
        self.dlq_sorted_set_key = f"{DRAMATIQ_NAMESPACE}:{queue_name}.XQ"
        self.dlq_msgs_key = f"{DRAMATIQ_NAMESPACE}:{queue_name}.XQ.msgs"
        self.msgs_key = f"{DRAMATIQ_NAMESPACE}:{queue_name}.msgs"

    def print_dlq(self, n_items: int = 100, print_details=False):
        # Fetch message IDs from the DLQ sorted set
        message_ids: list[bytes] = self.redis_client.zrange(self.dlq_sorted_set_key, 0, n_items - 1)

        print(f"Fetched {len(message_ids)} messages from the DLQ")

        if print_details:
            # Iterate over each message
            for message_id in message_ids:
                # Decode the message ID
                message_id_str = message_id.decode("utf-8")

                # Get the message data
                message_data = self.redis_client.hget(self.dlq_msgs_key, message_id)
                if message_data is None:
                    print(f"No message data found for message ID: {message_id_str}")
                    continue

                # Decode the message
                message = dramatiq.Message.decode(message_data)

                # Check if the message has failed
                retries = message.options.get("retries", 0)
                traceback = message.options.get("traceback")

                print(f"Message ID: {message_id_str}")
                if traceback:
                    # Message has failed
                    print(f"Found failed message: {message.message_id}")
                    # Optional: Inspect the traceback or other details
                    print(f"Traceback: {traceback}")
                    print(f"Message: {message}")
                else:
                    print(f"Message: {message}")

    def print_queue(self, n_items: int = 100, print_details=False):
        # Fetch all messages from the messages hash
        messages = self.redis_client.hgetall(self.msgs_key)

        print(f"Fetched {len(messages)} messages from the queue")

        if print_details:
            # Limit the number of messages printed
            count = 0
            for message_id_bytes, message_data_bytes in messages.items():
                if count >= n_items:
                    break
                # Decode message ID and data
                message_id_str = message_id_bytes.decode("utf-8")
                message_data = message_data_bytes

                # Decode the message using Dramatiq
                message = dramatiq.Message.decode(message_data)
                print(f"Message ID: {message_id_str}")
                print(f"Message: {message}")
                count += 1

    def requeue_message(self, message_id: str):
        # Convert message_id to bytes
        message_id_bytes = message_id.encode("utf-8")

        # Get the message data
        message_data = self.redis_client.hget(self.dlq_msgs_key, message_id_bytes)

        if message_data is None:
            print(f"No message found with ID: {message_id}")
            return

        # Decode the message
        message = dramatiq.Message.decode(message_data)

        # Reset retries and remove traceback to requeue the message
        message.options["retries"] = 0
        message.options.pop("traceback", None)

        # Enqueue the message back to the broker
        self.redis_broker.enqueue(message)
        print(f"Requeued message: {message.message_id}")

        # Remove the old message from the messages hash and sorted set
        self.redis_client.hdel(self.dlq_msgs_key, message_id_bytes)
        self.redis_client.zrem(self.dlq_sorted_set_key, message_id_bytes)

    def retry_dlq(self, n_items: int = 100):
        # Fetch message IDs from the DLQ sorted set
        message_ids = self.redis_client.zrange(self.dlq_sorted_set_key, 0, n_items - 1)

        print(f"Found {len(message_ids)} messages in DLQ to requeue.")

        # Iterate over each message
        for message_id in message_ids:
            # Decode message ID to string
            message_id_str = message_id.decode("utf-8")

            self.requeue_message(message_id_str)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dramatiq Queue Handler CLI")
    parser.add_argument("--queue", default="default", help="Name of the queue")
    parser.add_argument("--stage", default="dev", help="Stage (e.g., dev, prod)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: print-queue
    parser_print_queue = subparsers.add_parser("print-queue", help="Print messages in the queue")
    parser_print_queue.add_argument("--details", action="store_true", help="Print message details")
    parser_print_queue.add_argument("--n-items", type=int, default=100, help="Number of items to display")

    # Command: print-dlq
    parser_print_dlq = subparsers.add_parser("print-dlq", help="Print messages in the DLQ")
    parser_print_dlq.add_argument("--details", action="store_true", help="Print message details")
    parser_print_dlq.add_argument("--n-items", type=int, default=100, help="Number of items to display")

    # Command: requeue-message
    parser_requeue_message = subparsers.add_parser("requeue-message", help="Requeue a single message")
    parser_requeue_message.add_argument("message_id", help="ID of the message to requeue")

    # Command: retry-dlq
    parser_retry_dlq = subparsers.add_parser("retry-dlq", help="Requeue messages in the DLQ")
    parser_retry_dlq.add_argument("--n-items", type=int, default=100, help="Number of items to requeue")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        exit(1)

    STAGE = args.stage

    # Load environment variables
    load_dotenv(dotenv_path=f".env.{STAGE}")

    queue_name = args.queue
    queue_handler = DramatiqQueueHandler(queue_name)

    if args.command == "print-queue":
        queue_handler.print_queue(n_items=args.n_items, print_details=args.details)
    elif args.command == "print-dlq":
        queue_handler.print_dlq(n_items=args.n_items, print_details=args.details)
    elif args.command == "requeue-message":
        queue_handler.requeue_message(args.message_id)
    elif args.command == "retry-dlq":
        queue_handler.retry_dlq(n_items=args.n_items)
    else:
        parser.print_help()
