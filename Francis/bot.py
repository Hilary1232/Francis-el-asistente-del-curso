import pandas as pd
import re
import nltk
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import modelo
import requests
from flask import Flask, request
from flask_restful import Api
from nltk.stem import wordnet
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from sklearn.metrics import pairwise_distances
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

# Crear motor para conectarse a SQLite3
app = Flask(__name__)
api = Api(app)
BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'


def normalizar(texto):
    texto = str(texto).lower()
    spl_char_text = re.sub(r'[^a-z0-9]', ' ', texto)
    tokens = nltk.word_tokenize(spl_char_text)
    lema = wordnet.WordNetLemmatizer()
    tags_list = nltk.pos_tag(tokens, tagset=None)
    lema_words = []
    for token, pos_token in tags_list:
        if pos_token.startswith('V'):
            pos_val = 'v'
        elif pos_token.startswith('J'):
            pos_val = 'a'
        elif pos_token.startswith('R'):
            pos_val = 'r'
        else:
            pos_val = 'n'
        lema_token = lema.lemmatize(token, pos_val)
        lema_words.append(lema_token)
    return " ".join(lema_words)


def armar_respuesta(texto):
    engine = modelo.engine
    conn = engine.connect()
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y %H:%M")
    df = pd.read_sql_query('SELECT * FROM guion WHERE fecha_envio < "' + date_time + '" or fecha_envio = "";', conn)
    df.head()
    df['lemmatized_text'] = df['contexto']
    print('lemmatized_text')
    tfidf = TfidfVectorizer()
    x_tfidf = tfidf.fit_transform(df['lemmatized_text'].values.astype('U')).toarray()
    df_tfidf = pd.DataFrame(x_tfidf, columns=tfidf.get_feature_names())
    df_tfidf.head()
    lemma = normalizar(texto)
    tf = tfidf.transform([lemma]).toarray()
    cos = 1 - pairwise_distances(df_tfidf, tf, metric="cosine")
    index_value = cos.argmax()
    print(index_value)
    conn.close()
    return [df['respuesta'].loc[index_value], df['sticker'].loc[index_value], df['imagen'].loc[index_value],
            df['documento'].loc[index_value]]


# función que recupera id de chat
def obtener_chat_id(data):
    chat_id = data['message']["chat"]["id"]
    return chat_id


# función que recupera id de chat
def obtener_usuario(data):
    usuario = data['message']["chat"]["username"]
    return usuario


# función que recupera el mensaje de texto
def obtener_mensaje(data):
    mensaje = data["message"]["text"]
    return mensaje


# envía el mensaje de vuelta al usuario
def enviar_mensaje(chat_id, mensaje):
    respuesta = ""
    print("HERE!", mensaje[2])
    if mensaje[2] == "":
        params = {"chat_id": chat_id, "text": mensaje[0]}
        response = requests.post(BOT_URL + "sendMessage", data=params)
        respuesta = response
    if mensaje[1] is not None:
        stickerinfo = {"chat_id": chat_id, "sticker": mensaje[1]}
        sticker = requests.post(BOT_URL + "sendSticker", data=stickerinfo)
        respuesta = sticker
    if mensaje[2] is not None:
        picinfo = {"chat_id": chat_id, "caption": mensaje[0], "photo": mensaje[2]}
        imagen = requests.post(BOT_URL + "sendPhoto", data=picinfo)
        respuesta = imagen

    return str(respuesta)


def enviar_correo(respuesta, usuario, mensaje):
    sender_email_address = 'francisbotnotifs@gmail.com'
    sender_email_password = 'francisbot123'
    qry = "SELECT email from usuario"
    engine = modelo.engine
    conn = engine.connect()
    cons = conn.execute(qry).fetchall()
    emails = [list(i) for i in cons]
    recipients = sum(emails, [])
    print(recipients)
    conn.close()
    receiver_email_address = ", ".join(recipients)

    email_subject_line = 'Francis ha respondido un mensaje'

    msg = MIMEMultipart()
    msg['From'] = sender_email_address
    msg['To'] = receiver_email_address
    msg['Subject'] = email_subject_line
    email_body = 'Mensaje recibido :  ' + mensaje + ' por ' + usuario + '\n\nRespuesta del bot' + ':   ' + respuesta
    print(email_body)
    msg.attach(MIMEText(email_body, 'plain'))

    email_content = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(sender_email_address, sender_email_password)
    server.sendmail(sender_email_address, msg['To'].split(","), email_content)
    server.quit()
    return "todo bien"


def loggear_respuesta(mensaje, respuesta):
    engine = modelo.engine
    conn = engine.connect()
    query = "INSERT INTO log(mensaje,respuesta, sticker, imagen, documento, fecha) VALUES(?,?,?,?,?,datetime('now'));"
    task = (mensaje, respuesta[0], respuesta[1], respuesta[2], respuesta[3])
    status = conn.execute(query, task)
    conn.close()
    return status


# Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
def lookup(data):
    mensaje = obtener_mensaje(data)
    usuario = obtener_usuario(data)
    respuesta = armar_respuesta(mensaje)
    status = enviar_mensaje(obtener_chat_id(data), respuesta)
    enviar_correo(respuesta[0], usuario, mensaje)
    loggear_respuesta(mensaje, respuesta)
    return status


@app.route('/', methods=['POST'])
def main():
    data = request.json
    status = lookup(data)
    return status  # status 200 OK por defecto


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
