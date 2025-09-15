# auth_service/models.py

import time
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Integer, String,
                        create_engine)
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import get_env_vars here
from shared.config import get_config, get_env_vars  # ADDED get_env_vars

# Load config (from config.yml)
config = get_config()

# Load environment variables (from .env file)
env = get_env_vars()  # NEW LINE: Get the env vars into a separate 'env' variable

# Database setup
DATABASE_URL = (
    f"mysql+mysqlconnector://{env.mysql_user}:{env.mysql_password}@"
    f"{env.MYSQL_HOST}:{env.MYSQL_PORT}/{config.databases.mysql.user_db_name}"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


# User Model Definition
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_active={self.is_active})>"


# Function to create tables
def create_db_tables():
    """
    Creates database tables with a retry mechanism to handle startup race conditions.
    """
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            # Attempt to connect and create tables
            Base.metadata.create_all(bind=engine)
            print("Successfully connected to the database and created tables.")
            return  # Exit the function on success
        # --- CATCH A MORE GENERAL EXCEPTION ---
        except Exception as e:
            print(
                f"Database connection failed (Attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to the database.")
                raise  # Re-raise the last exception if all retries fail


# Example usage (for testing models)
if __name__ == "__main__":
    create_db_tables()
    print("User table created successfully or already exists.")

    # You can add some test data creation here if needed
    # db = SessionLocal()
    # try:
    #     new_user = User(username="testuser", hashed_password="hashedpassword123", is_active=True)
    #     db.add(new_user)
    #     db.commit()
    #     db.refresh(new_user)
    #     print(f"Added user: {new_user}")
    # except Exception as e:
    #     db.rollback()
    #     print(f"Error adding user: {e}")
    # finally:
    #     db.close()
