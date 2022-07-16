from sqlalchemy import ForeignKey, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from dotenv import load_dotenv
import os

load_dotenv()

base = declarative_base()
engine = sa.create_engine(os.getenv("DATABASE_URL"))
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker(bind=engine))
