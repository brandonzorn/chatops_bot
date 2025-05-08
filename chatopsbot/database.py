from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_NAME
from models import Base

Path("sqlite").mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///sqlite/{DATABASE_NAME}.db"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
