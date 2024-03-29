import os

from dotenv import load_dotenv

dotenv_path = ".env.production" if os.getenv("STAGE") == "prod" else ".env.development"
load_dotenv(dotenv_path=dotenv_path)

MONGO_URI = os.environ["MONGO_URI"]
MONGO_DATABASE = os.environ["MONGO_DATABASE"]
SCRAPER_FEED_HANDLED_TOPIC_ARN = os.environ["SCRAPER_FEED_HANDLED_TOPIC_ARN"]
PRICING_FEED_HANDLED_TOPIC_ARN = os.environ["PRICING_FEED_HANDLED_TOPIC_ARN"]
BOOK_FEED_HANDLED_TOPIC_ARN = os.environ["BOOK_FEED_HANDLED_TOPIC_ARN"]
