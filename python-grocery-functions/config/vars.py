import os

from dotenv import load_dotenv

dotenv_path = ".env.prod" if os.getenv("STAGE") == "prod" else ".env.dev"
load_dotenv(dotenv_path=dotenv_path)

# SCRAPER_FEED_HANDLED_TOPIC_ARN = os.environ["SCRAPER_FEED_HANDLED_TOPIC_ARN"]
# PRICING_FEED_HANDLED_TOPIC_ARN = os.environ["PRICING_FEED_HANDLED_TOPIC_ARN"]
# BOOK_FEED_HANDLED_TOPIC_ARN = os.environ["BOOK_FEED_HANDLED_TOPIC_ARN"]

# MongoDB variables removed - using PostgreSQL now
SCRAPER_FEED_HANDLED_TOPIC_ARN = ""
PRICING_FEED_HANDLED_TOPIC_ARN = ""
BOOK_FEED_HANDLED_TOPIC_ARN = ""

POSTGRES_URL = os.environ["POSTGRES_URL"]
