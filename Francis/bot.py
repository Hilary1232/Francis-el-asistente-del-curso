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
            pos_val = 'v'
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
    engine = modelo.engine
    conn = engine.connect()
    df = pd.read_sql_table("guion", conn)
    df.head()
    df['lemmatized_text'] = df['contexto']
    tfidf = TfidfVectorizer()
    x_tfidf=tfidf.fit_transform(df['lemmatized_text'].values.astype('U')).toarray()
    df_tfidf = pd.DataFrame(x_tfidf,columns=tfidf.get_feature_names())
    df_tfidf.head()
    lemma = normalizar(texto)
    tf = tfidf.transform([lemma]).toarray()
    cos = 1-pairwise_distances(df_tfidf, tf, metric="cosine")
    index_value = cos.argmax()
    print(index_value)
    conn.close()
    return [df['respuesta'].loc[index_value], df['sticker'].loc[index_value], df['img_src'].loc[index_value]]

# función que recupera id de chat
def get_chat_id(update):
    chat_id = update['message']["chat"]["id"]
    return chat_id


# función que recupera el mensaje de texto
def get_message_text(update):
    message_text = update["message"]["text"]
    return message_text


# envía el mensaje de vuelta al usuario
def send_message(chat_id, message): #message_text es la respuesta del bot
    answer = ""
    print("HERE!",message[2])
    if(message[2] == ""):
        params = {"chat_id": chat_id, "text": message[0]}
        response = requests.post(BOT_URL + "sendMessage", data=params)
        answer = response
    if(message[1] != None):
        stickerinfo = {"chat_id": chat_id,"sticker": message[1]}
        sticker_response = requests.post(BOT_URL + "sendSticker", data=stickerinfo)
        answer = sticker_response
    if (message[2] != None):
        picinfo = {"chat_id": chat_id, "caption":message[0], "photo": message[2]}
        pic_response = requests.post(BOT_URL + "sendPhoto", data=picinfo)
        answer = pic_response

    return str(answer)


def send_email(answer,message):
    sender_email_address = 'francisbotnotifs@gmail.com'
    sender_email_password = 'francisbot123'
    qry = "SELECT email from usuario"
    engine = modelo.engine
    conn = engine.connect()
    cons = conn.execute(qry).fetchall()
    emails = [list(i) for i in cons]
    recipients = sum(emails,[])
    print(recipients)
    conn.close()
    receiver_email_address = ", ".join(recipients)

    email_subject_line = 'Mensaje enviado por el Bot Francis'

    msg = MIMEMultipart()
    msg['From'] = sender_email_address
    msg['To'] = receiver_email_address
    msg['Subject'] = email_subject_line
    email_body = 'Mensaje:  '+message+'\n\nRespuesta del bot'+':   '+answer
    print(email_body)
    msg.attach(MIMEText(email_body, 'plain'))

    email_content = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(sender_email_address, sender_email_password)
    server.sendmail(sender_email_address, msg['To'].split(","), email_content)
    server.quit()
    return "todo bien"


def log_answer(message, answer):
    engine = modelo.engine
    conn = engine.connect()
    query = "INSERT INTO log(mensaje,respuesta, sticker, img_src, date) VALUES(?,?,?,?,datetime('now'));"
    task = (message, answer[0], answer[1], answer[2])
    status = conn.execute(query, task)
    conn.close()
    return status

#Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
def lookup(data):
    message = get_message_text(data)
    respuesta = armar_respuesta(message)
    answer = send_message(get_chat_id(data), respuesta)
    send_email(respuesta[0], message)
    log_answer(message, respuesta)
    return answer


@app.route('/', methods=['POST'])
def main():
    data = request.json
    status = lookup(data)
    return status  # status 200 OK por defecto


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)