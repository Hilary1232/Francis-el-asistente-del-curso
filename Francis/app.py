from flask import Flask, request, render_template, make_response
from flask_restful import Resource, Api
import modelo
import json
import collections
import requests
from bottle import (
    run, post, response, request as bottle_request
)

#Crear motor para conectarse a SQLite3
engine = modelo.engine
session = modelo.Session()
app = Flask(__name__)
api = Api(app)

BOT_URL = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/'

@app.route('/descargar', methods=["POST"])
def descargarArchivoCsv():
    request_file = request.files['data_file']
    if not request_file:
        return "No se seleccionó ningún archivo"

    file_contents = request_file.stream.read().decode("utf-8")

    result = transformar(file_contents)

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=guión.csv"
    return response

def transformar(text_file_contents):
    return text_file_contents.replace("=", ",")

def get_chat_id(data):
    """
    Method to extract chat id from telegram request.
    """
    chat_id = data['message']['chat']['id']

    return chat_id

def get_message(data):
    """
    Method to extract message id from telegram request.
    """
    message_text = data['message']['text']

    return message_text

def send_message(prepared_data):
    """
    Prepared data should be json which includes at least `chat_id` and `text`
    """
    message_url = BOT_URL + 'sendMessage'
    requests.post(message_url, json=prepared_data)  # don't forget to make import requests lib

def change_text_message(text):
    """
    To enable turning our message inside out
    """
    return text[::-1]

def prepare_data_for_answer(data):
    answer = change_text_message(get_message(data))

    json_data = {
        "chat_id": get_chat_id(data),
        "text": answer,
    }

    return json_data

@post('/')
def bot_question():
    data = bottle_request.json

    answer_data = prepare_data_for_answer(data)
    send_message(answer_data)  # <--- function for sending answer

    return response  # status 200 OK by default

@app.route('/', methods=['GET']) #Cuando el href solo tenga un '/', que llegue a esta funcion y ejecute
def home():
    return render_template('index.html')

@app.route('/cursos', methods=['GET']) #Cuando la solicitud tiene un /cursos, devuelva la pagina de cursos
def cursos():
    return render_template('cursos.html')

@app.route('/cursos-get') #Es llamada por Javascript, para mostrar la tabla de cursos de la base. 
def getcursos():
    #Ejecutar consulta y devolver datos JSON
    conn = engine.connect()
    query = conn.execute("SELECT * FROM curso")
    cursos = query.fetchall()
    lista_cursos = []
    for curso in cursos:
        d = collections.OrderedDict()
        d['id'] = curso.id
        d['codigo'] = curso.codigo
        d['nombre'] = curso.nombre
        d['descripcion'] = curso.descripcion
        d['ciclo'] = curso.ciclo
        d['anno'] = curso.anno
        lista_cursos.append(d)
        
    js = json.dumps(lista_cursos)
    return js

if __name__ == '__main__':
    run(host='localhost', port=5000, debug=True)

