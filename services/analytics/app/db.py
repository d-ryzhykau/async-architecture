from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import settings

engine = create_engine(url=str(settings.database_url))
Session = sessionmaker(engine)
