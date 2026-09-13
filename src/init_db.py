from src.database import Base, engine
from src.models import OAuthAccount


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()