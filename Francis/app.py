from flask import Flask, request, render_template, make_response
from flask_restful import Resource, Api
import modelo
import json
import collections
import os
import cgitb; cgitb.enable()
#Crear motor para conectarse a SQLite3
engine = modelo.engine
session = modelo.Session()
app = Flask(__name__)
api = Api(app)


@app.route('/descargar', methods=["POST"])
def descargar_archivo_csv():
    request_file = request.files['myfile']
    if not request_file:
        return "No se seleccionaron archivos"

    file_contents = request_file.stream.read().decode("utf-8")

    result = transformar(file_contents)

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename="+request_file.filename
    return response


@app.route('/crear-curso', methods=["POST"])
def crear_curso():
    curso = request.form['curso']
    conn = engine.connect()
    return curso



@app.route('/cargar', methods=["POST"])
def cargar_archivo_csv():
    #Obtener nombre de archivo
    fileitem = request.files['myfile']
    # Probar si se cargo el archivo
    if fileitem.filename:
        # dejar solo el nombre del archivo para evitar ataques traversales de directorio
        fn = os.path.basename(fileitem.filename)
        archivo = open(fn, 'wb')
        archivo.write(fileitem.read())
        message = 'El archivo"' + fn + '" ha sido cargado exitosamente'

    else:
        message = 'No se ha cargado ningun archivo'
    print(message)
    return render_template('home.html')

def transformar(text_file_contents):
    return text_file_contents.replace("=", ",")


@app.route('/', methods=['GET']) #Cuando el href solo tenga un '/', que llegue a esta funcion y ejecute
def index():
    return render_template('index.html')


@app.route('/home', methods=['GET','post']) #Cuando el href tenga un '/home', que llegue a esta funcion y ejecute
def home():
    return render_template('home.html')


@app.route('/cursos', methods=['GET']) #Cuando la solicitud tiene un /cursos, devuelva la pagina de cursos
def cursos():
    return render_template('cursos.html')


@app.route('/get-key',methods=['POST'])
def get_key():
    bot_key = request.form['key']
    #key = 1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ


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

app.run(host='localhost', port=5001, debug=True)

