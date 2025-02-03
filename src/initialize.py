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
        self.openai_client = (
            self._init_deepseek_client()
            if self.config["ai_provider"] == "deepseek"
            else self._init_openai_client()
        )
        self.mongodb_client = self._init_mongodb_client()

    def initialize_logging(self):
        """Initializes and configures logging."""
        logger = lg.getLogger()
        logger.info("Initializing logging")

        # Clear existing handlers
        logger.handlers = []

        # Console (StreamHandler) setup
        console_handler = lg.StreamHandler()
        console_formatter = lg.Formatter(
            "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # FileHandler setup
        file_handler = lg.FileHandler("application.log")
        file_formatter = lg.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # Set the logging level
        logger.setLevel(lg.INFO)

        logger.info("Initialized logging")

        # Ensure uvicorn logs use the same handlers
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

    def _init_deepseek_client(self):
        """Initializes the DeepSeek client."""
        self.logger.info("Initializing DeepSeek client")
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"
        )
        self.logger.info("Initialized DeepSeek client")
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
