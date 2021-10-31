from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine('sqlite:///:memory:', echo=False)

base_session = sessionmaker(autocommit = False, autoflush = True, bind = engine)
session = scoped_session(base_session)

Base = declarative_base()
Base.query = session.query_property()
