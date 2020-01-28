#!/usr/bin/python
import datetime
import os
from time import sleep
import modelo
import requests
from flask import Flask, request
from flask_restful import Api
#Crear motor para conectarse a SQLite3
app = Flask(__name__)
api = Api(app)
BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'


def send_file(chat_id, message,text): #message_text es la respuesta del bot
    filepath = os.path.join('static/files',message)
    files = {'document': open(filepath, 'rb')}
    doc = {"chat_id": chat_id, "caption": text}
    enviado = requests.post(BOT_URL + "sendDocument", data=doc, files=files)
    respuesta = enviado
    return respuesta
      


def send_message(chat_id, message): #message_text es la respuesta del bot
    params = {"chat_id": chat_id, "text": message}
    response = requests.post(BOT_URL + "sendMessage", data=params)
    return str(response)


def send_sticker(chat_id, message):
    filepath = os.path.join('static/stickers', message)
    files = {'sticker': open(filepath, 'rb')}
    stickerinfo = {"chat_id": chat_id}
    sticker = requests.post(BOT_URL + "sendSticker", data=stickerinfo, files=files)
    respuesta = sticker
    return respuesta

def send_img(chat_id, pic, text):
    filepath = os.path.join('static/img', pic)
    files = {'photo': open(filepath, 'rb')}
    picinfo = {'chat_id': chat_id, 'caption': text}
    imagen = requests.post(BOT_URL + "sendPhoto", data=picinfo, files=files)
    respuesta = imagen
    return respuesta

def get_groups():
    engine = modelo.engine
    qry = 'SELECT grupo_id FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    groups = sum(temp, [])
    conn.close()
    return groups


def get_times():
    engine = modelo.engine
    qry = 'SELECT fecha_envio FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    times = sum(temp, [])
    conn.close()
    return times


def get_texts():
    engine = modelo.engine
    qry = 'SELECT respuesta FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    texts = sum(temp, [])
    conn.close()
    return texts


def get_docs():
    engine = modelo.engine
    qry = 'SELECT documento FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    docs = sum(temp, [])
    conn.close()
    return docs

def get_stickers():
    engine = modelo.engine
    qry = 'SELECT sticker FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    docs = sum(temp, [])
    conn.close()
    return docs

def get_imgs():
    engine = modelo.engine
    qry = 'SELECT imagen FROM guion WHERE fecha_envio != ""'
    conn = engine.connect()
    cons = conn.execute(qry)
    temp = [list(i) for i in cons]
    docs = sum(temp, [])
    conn.close()
    return docs

#Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
def lookup():
    times = get_times()
    texts = get_texts()
    chat_ids = get_groups()
    docs = get_docs()
    stickers = get_stickers()
    imgs = get_imgs()
    answer = ""
    while True:
        for time in times:
            now = datetime.datetime.now()
            date = now.strftime("%d/%m/%Y %H:%M")
            if date == time:
                message = texts[times.index(time)]
                chat_id = chat_ids[times.index(time)]
                doc = docs[times.index(time)]

                if doc != "":
                    send_file(chat_id, docs[times.index(time)], message)

                if sticker != "":
                    send_sticker(chat_id,stickers[times.index(time)])
                    send_message(chat_id,message)

                if img!="":
                    send_img(chat_id, imgs[times.index(time)], message)
                else:
                    send_message(chat_id,message)
                
              
        sleep(60)
    return answer


lookup()
