# shared/config.py

import os
from types import SimpleNamespace

import yaml
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.yml"
        )
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        def dict_to_simplenamespace(d):
            if isinstance(d, dict):
                return SimpleNamespace(
                    **{k: dict_to_simplenamespace(v) for k, v in d.items()}
                )
            return d

        self.config = dict_to_simplenamespace(config_data)

        self.env = SimpleNamespace(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            mysql_user=os.getenv("MYSQL_USER"),
            mysql_password=os.getenv("MYSQL_PASSWORD"),
            MYSQL_HOST=os.getenv("MYSQL_HOST", self.config.databases.mysql.host),
            MYSQL_PORT=os.getenv("MYSQL_PORT", str(self.config.databases.mysql.port)),
            MONGODB_HOST=os.getenv("MONGODB_HOST", self.config.databases.mongodb.host),
            MONGODB_PORT=os.getenv(
                "MONGODB_PORT", str(self.config.databases.mongodb.port)
            ),
            # --- MongoDB credentials ---
            mongodb_user=os.getenv("MONGODB_USER", None),
            mongodb_password=os.getenv("MONGODB_PASSWORD", None),
            # --- Redis configuration ---
            REDIS_HOST=os.getenv("REDIS_HOST", self.config.databases.redis.host),
            REDIS_PORT=os.getenv("REDIS_PORT", str(self.config.databases.redis.port)),
            REDIS_DB=os.getenv("REDIS_DB", str(self.config.databases.redis.db)),
            # --- AWS configuration ---
            AWS_REGION=os.getenv("AWS_REGION", self.config.aws.region),
            S3_USER_IMAGES_BUCKET=os.getenv(
                "S3_USER_IMAGES_BUCKET", self.config.aws.s3.user_images_bucket_name
            ),
            SQS_QUEUE_URL=os.getenv("SQS_QUEUE_URL", ""),
        )

        # This part constructs the MySQL URL for self.config.databases.mysql.url.
        # Ensure that other parts of your app that use MySQL also refer to `env.MYSQL_HOST` etc.
        self.config.databases.mysql.url = (
            f"mysql+mysqlconnector://{self.env.mysql_user}:"
            f"{self.env.mysql_password}@{self.env.MYSQL_HOST}:{self.env.MYSQL_PORT}/"
            f"{self.config.databases.mysql.user_db_name}"
        )

        # OpenAI API Key Check - ensure it's not None if mandatory
        if not self.env.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")


# Instantiate the config globally or get it via a function
def get_config():
    return AppConfig().config


def get_env_vars():
    return AppConfig().env


# Example usage (for testing purposes, not typically in production code directly)
if __name__ == "__main__":
    config = get_config()
    env = get_env_vars()
    print("Loaded Config:")
    print(f"App Name: {config.app_settings.app_name}")
    print(f"JWT Algorithm: {config.jwt.algorithm}")
    print(f"MySQL Host (from env or config): {env.MYSQL_HOST}")
    print(f"MongoDB Host (from env or config): {env.MONGODB_HOST}")
    print(f"MySQL URL: {config.databases.mysql.url}")
    print("\nLoaded Environment Variables (sensitive info omitted for display):")
    print(f"JWT Secret Key Loaded: {'Yes' if env.jwt_secret_key else 'No'}")
    print(f"OpenAI API Key Loaded: {'Yes' if env.openai_api_key else 'No'}")
    print(f"MongoDB User Loaded: {env.mongodb_user}")  # Check if it's None or a value
