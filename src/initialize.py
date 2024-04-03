import logging as lg
import os
import yaml
from openai import OpenAI
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv

load_dotenv()


class Initializer:
    def __init__(self):
        self.logger = self.initialize_logging()
        self.config = self._init_config()
        self.openai_client = self._init_openai_client()
        self.mongodb_client = self._init_mongodb_client()

    def initialize_logging(self):
        """Initializes and configures logging."""
        logger = lg.getLogger()
        logger.info("Initializing logging")
        logger.handlers = []
        handler = lg.StreamHandler()
        formatter = lg.Formatter(
            "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(lg.INFO)
        logger.info("Initialized logging")
        lg.getLogger("uvicorn.error").handlers = logger.handlers
        return logger

    def _init_config(self):
        """Loads the application configuration from a YAML file."""
        yaml_config_path = os.getenv("CONFIG_PATH")
        with open(yaml_config_path, "r") as stream:
            config = yaml.safe_load(stream)
        self.logger.info("Configuration loaded")
        return config

    def _init_openai_client(self):
        """Initializes the OpenAI client."""
        self.logger.info("Initializing OpenAI client")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger.info("Initialized OpenAI client")
        return client

    def _init_mongodb_client(self):
        """Initializes the MongoDB client."""
        self.logger.info("Initializing MongoDB client")
        URI = os.getenv("MONGODB_URI")
        client = MongoClient(URI)
        try:
            client.admin.command("ping")
            self.logger.info("Initialized MongoDB client")
        except Exception as e:
            self.logger.info(f"Error initializing MongoDB client: {e}")
        return client
