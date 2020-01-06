from flask import Flask, request, render_template, make_response,jsonify
from flask_restful import Resource, Api
import modelo
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
global message,botAnswer

#Crear motor para conectarse a SQLite3
engine = modelo.engine
session = modelo.Session()
app = Flask(__name__)
api = Api(app)
BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'


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
    send_email(botAnswer, message)
    return str(response)

#Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
def lookup(data):
  message = get_message_text(data)
  answer = send_message(get_chat_id(data),'Holaa!!')

def send_email(answer,message):
    sender_email_address = 'hilarygonalez@gmail.com'
    sender_email_password = 'Arcoiris10'
    receiver_email_address = 'hilarygonzalez10@hotmail.com'

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

def lookup(data): #Se supone que aqui es la funcion donde va a entrar al csv o a la base y busca la respuesta adecuada
  global message, botAnswer
  message = get_message_text(data)
  botAnswer = 'Esto es una prueba!!'
  answer = send_message(get_chat_id(data),botAnswer)
  return answer


@app.route('/', methods=['POST'])
def main():
    data = request.json
    status = lookup(data)
    return status  # status 200 OK por defecto


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)