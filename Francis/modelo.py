from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
import sqlite3

Base = declarative_base()


class Curso(Base):
    __tablename__ = "curso"
    id = Column('id', Integer, primary_key=True)
    curso = Column('curso', String)


class Guion(Base):
    __tablename__ = "guion"
    id = Column('id', Integer, primary_key=True)
    curso = Column('tema', String)
    contexto = Column('contexto', String)
    respuesta = Column('respuesta', String)
    sticker = Column('sticker', String)
    imagen = Column('imagen', String)
    documento = Column('documento', String)
    fecha_envio = Column('fecha_envio', String)


class Log(Base):
    __tablename__ = "log"
    id = Column('id', Integer, primary_key=True)
    curso = Column('mensaje', String)
    respuesta = Column('respuesta', String)
    sticker = Column('sticker', String)
    imagen = Column('imagen', String)
    documento = Column('documento', String)
    fecha = Column('fecha', String)

class Usuario(Base, UserMixin):
    __tablename__ = "usuario"
    id = Column('id', Integer, primary_key=True)
    username = Column('username', String, unique=True)
    email = Column('email', String, unique=True)
    password = Column('password', String, unique=True)
    bot_token = Column('bot_token', String, default='1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ')
    img_src = Column('img_src', String)

engine = create_engine('sqlite:///db/francis.db')
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()
session.close()