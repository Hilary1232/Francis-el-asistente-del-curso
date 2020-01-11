from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
import sqlite3

Base = declarative_base()


class Curso(Base):
    __tablename__ = "curso"
    id = Column('id', Integer, primary_key=True)
    codigo = Column('codigo', String)
    nombre = Column('nombre', String)
    descripcion = Column('descripcion', String)
    ciclo = Column('ciclo', String)
    anno = Column('anno', String)


class Usuario(Base, UserMixin):
    __tablename__ = "usuario"
    id = Column('id', Integer, primary_key=True)
    username = Column('username', String, unique=True)
    email = Column('email', String, unique=True)
    password = Column('password', String, unique=True)
    bot_token = Column('bot_token', String)
    img_src = Column('img_src', String)

engine = create_engine('sqlite:///db/francis.db')
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()
session.close()