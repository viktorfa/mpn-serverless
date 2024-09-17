import os
from dotenv import load_dotenv
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent

dotenv_path = (
    BASE_PATH / ".env.prod" if os.getenv("STAGE") == "prod" else BASE_PATH / ".env.prod"
)
load_dotenv(dotenv_path=dotenv_path)

MONGO_URI = os.environ["MONGO_URI"]
MONGO_DATABASE = os.environ["MONGO_DATABASE"]
OPEN_AI_KEY = os.environ["OPEN_AI_KEY"]

# Because this env variable doesn't work when local
ML_MODELS_BUCKET = (
    os.getenv("ML_MODELS_BUCKET") or "python-mpn-ml-dev-mlmodelsbucket-us16pfe040o3"
)
