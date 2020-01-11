import csv
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

#Crear motor para conectarse a SQLite3
engine = modelo.engine
session = modelo.Session()
app = Flask(__name__)
api = Api(app)
BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'


def normalizar(texto):
    texto = str(texto).lower()
    spl_char_text = re.sub(r'[^a-z0-9]', ' ', texto)
    tokens=nltk.word_tokenize(spl_char_text)
    lema = wordnet.WordNetLemmatizer()
    tags_list = nltk.pos_tag(tokens, tagset=None)
    lema_words=[]
    for token, pos_token in tags_list:
        if pos_token.startswith('V'):
            pos_val - 'v'
        elif pos_token.startswith('J'):
            pos_val='a'
        elif pos_token.startswith('R'):
            pos_val='r'
        else:
            pos_val='n'
        lema_token=lema.lemmatize(token,pos_val)
        lema_words.append(lema_token)
    return " ".join(lema_words)



def armar_respuesta(texto):
    df = pd.read_csv("static/cursos/Intro y Taller/guion1.csv")
    df.head()
    df['lemmatized_text'] = df['nombre']
    tfidf = TfidfVectorizer()
    x_tfidf=tfidf.fit_transform(df['lemmatized_text'].values.astype('U')).toarray()
    df_tfidf = pd.DataFrame(x_tfidf,columns=tfidf.get_feature_names())
    df_tfidf.head()
    lemma = normalizar(texto)
    tf = tfidf.transform([lemma]).toarray()
    cos = 1-pairwise_distances(df_tfidf, tf, metric="cosine")
    index_value = cos.argmax()
    print(index_value)
    return df['descripcion'].loc[index_value]

# función que recupera id de chat
def get_chat_id(update):
    chat_id = update['message']["chat"]["id"]
    return chat_id


# función que recupera el mensaje de texto
def get_message_text(update):
    message_text = update["message"]["text"]
    return message_text


# envía el mensaje de vuelta al usuario
def send_message(chat_id, message_text): #message_text es la respuesta del bot
    params = {"chat_id": chat_id, "text": message_text}
    response = requests.post(BOT_URL + "sendMessage",data=params)
    return str(response)


def send_email(answer,message):
    sender_email_address = 'hilarygonalez@gmail.com'
    sender_email_password = 'Arcoiris10'
    receiver_email_address = 'm.venegasb98@gmail.com'

    email_subject_line = 'Mensaje enviado por el Bot Francis'

    msg = MIMEMultipart()
    msg['From'] = sender_email_address
    msg['To'] = receiver_email_address
    msg['Subject'] = email_subject_line

    email_body = 'Mensaje:  '+message+'\n\nRespuesta del bot'+':   '+answer
    msg.attach(MIMEText(email_body, 'plain'))

    email_content = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(sender_email_address, sender_email_password)

    server.sendmail(sender_email_address, receiver_email_address, email_content)
    server.quit()
    return ""


#Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
def lookup(data):
  message = get_message_text(data)
  respuesta = armar_respuesta(message)
  answer = send_message(get_chat_id(data), respuesta)
  answer = send_email(answer, message)
  return answer


@app.route('/', methods=['POST'])
def main():
    data = request.json
    status = lookup(data)
    return status  # status 200 OK por defecto


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)