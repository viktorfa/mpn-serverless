import os

from dotenv import load_dotenv

dotenv_path = ".env.production" if os.getenv("STAGE") == "prod" else ".env.development"
load_dotenv(dotenv_path=dotenv_path)

MONGO_HOST = os.getenv("MONGO_HOST", "0.0.0.0")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DATABASE = os.environ["MONGO_DATABASE"]
# Because this env variable doesn't work when local
ML_MODELS_BUCKET = (
    os.environ["ML_MODELS_BUCKET"] or "python-mpn-ml-dev-mlmodelsbucket-us16pfe040o3"
)
