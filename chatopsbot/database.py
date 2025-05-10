from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import (
    DATABASE_NAME,
    DATABASE_USER,
    USE_SQLITE_DATABASE,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
)
from models import Base

if USE_SQLITE_DATABASE:
    Path("sqlite").mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///sqlite/{DATABASE_NAME}.db"
else:
    DATABASE_URL = (
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@"
        f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}",
    )

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
