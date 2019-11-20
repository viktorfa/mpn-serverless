import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.production")


MONGO_HOST = os.getenv("MONGO_HOST", "0.0.0.0")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DATABASE = os.environ["MONGO_DATABASE"]
