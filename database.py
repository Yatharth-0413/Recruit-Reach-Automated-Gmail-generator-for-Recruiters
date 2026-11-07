
# import os
# from datetime import datetime

# from sqlalchemy import (
#     create_engine,
#     Column,
#     Integer,
#     String,
#     DateTime,
#     Text,
#     inspect,
#     text
# )
# from sqlalchemy.orm import declarative_base, sessionmaker


# # Database location
# os.makedirs("data", exist_ok=True)

# DATABASE_URL = "sqlite:///data/applications.db"

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )

# Base = declarative_base()


# # Application table
# class Application(Base):

#     __tablename__ = "applications"

#     id = Column(Integer, primary_key=True, index=True)

#     company = Column(String)
#     recruiter_name = Column(String)
#     recruiter_email = Column(String)
#     role = Column(String)

#     subject = Column(String)
#     thread_id = Column(String, unique=True)

#     status = Column(String, default="Sent")

#     sent_at = Column(DateTime, default=datetime.utcnow)

#     # First reply
#     replied_at = Column(DateTime, nullable=True)
#     reply_content = Column(Text, nullable=True)

#     # Reply tracking
#     reply_count = Column(Integer, default=0)

#     # Latest reply
#     last_reply_at = Column(DateTime, nullable=True)
#     last_reply_content = Column(Text, nullable=True)
#     last_reply_from = Column(String, nullable=True)


# # Create tables if they don't exist
# Base.metadata.create_all(bind=engine)


# # Migrate existing database safely
# def migrate_database():

#     inspector = inspect(engine)

#     columns = {
#         column["name"]
#         for column in inspector.get_columns("applications")
#     }

#     migrations = {
#         "reply_count": "INTEGER DEFAULT 0",
#         "last_reply_at": "DATETIME",
#         "last_reply_content": "TEXT",
#         "last_reply_from": "VARCHAR"
#     }

#     with engine.begin() as connection:

#         for column, definition in migrations.items():

#             if column not in columns:

#                 connection.execute(
#                     text(
#                         f"ALTER TABLE applications "
#                         f"ADD COLUMN {column} {definition}"
#                     )
#                 )

#     print("Database migration completed.")


# migrate_database()


# # Database session
# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )



import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    inspect,
    text
)
from sqlalchemy.orm import declarative_base, sessionmaker


# Database location
os.makedirs("data", exist_ok=True)

DATABASE_URL = "sqlite:///data/applications.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

Base = declarative_base()


# Application table
class Application(Base):

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    company = Column(String)
    recruiter_name = Column(String)
    recruiter_email = Column(String)
    role = Column(String)

    subject = Column(String)
    thread_id = Column(String, unique=True)

    status = Column(String, default="Sent")

    sent_at = Column(DateTime, default=datetime.utcnow)

    # First reply
    replied_at = Column(DateTime, nullable=True)
    reply_content = Column(Text, nullable=True)

    # Reply tracking
    reply_count = Column(Integer, default=0)

    # Latest reply
    last_reply_at = Column(DateTime, nullable=True)
    last_reply_content = Column(Text, nullable=True)
    last_reply_from = Column(String, nullable=True)

    # Automatically detected reply category
    reply_category = Column(String, default="Other", nullable=True)


# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


# Migrate existing database safely
def migrate_database():

    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("applications")
    }

    migrations = {
        "reply_count": "INTEGER DEFAULT 0",
        "last_reply_at": "DATETIME",
        "last_reply_content": "TEXT",
        "last_reply_from": "VARCHAR",
        "reply_category": "VARCHAR DEFAULT 'Other'"
    }

    with engine.begin() as connection:

        for column, definition in migrations.items():

            if column not in columns:

                connection.execute(
                    text(
                        f"ALTER TABLE applications "
                        f"ADD COLUMN {column} {definition}"
                    )
                )

    print("Database migration completed.")


migrate_database()


# Database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
