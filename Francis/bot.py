import requests
from bottle import (
    run, post, response, request as bottle_request
)
BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'


# create func that get chat id
def get_chat_id(update):
    chat_id = update['message']["chat"]["id"]
    return chat_id


# create function that get message text
def get_message_text(update):
    message_text = update["message"]["text"]
    return message_text

def send_message(chat_id, message_text):
    params = {"chat_id": chat_id, "text": message_text}
    response = requests.post(BOT_URL + "sendMessage", data=params)
    return response

def lookup(data): #Se supone que aqui es la funcion donde entra al csv o a la base y busca la respuesta adecuada
  message = get_message_text(data)
  answer = send_message(get_chat_id(data),'Hilary es una perra!!')
  return answer

@post('/')
def main():
    data = bottle_request.json
    status = lookup(data)
    return status  # status 200 OK by default

run(host='localhost', port=5000, debug=True)