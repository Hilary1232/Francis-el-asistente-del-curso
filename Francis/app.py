from flask_restful import Resource, Api
from flask import Flask, render_template, redirect, url_for, make_response, request
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import modelo
import csv
import json
import collections
import os
import cgitb;
from Francis.modelo import Usuario

cgitb.enable()

#Crear motor para conectarse a SQLite3
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    engine = modelo.engine
    session = modelo.Session()
    user = modelo.Usuario()
    return session.query(Usuario).get(int(user_id))


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET'])
def register():
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    engine = modelo.engine
    session = modelo.Session()
    username = request.form['username']
    print(username)
    user = session.query(Usuario).first()
    print(user)
    if user:
        if check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            return redirect(url_for('home'))

    return '<h1>Usuario o contraseña incorrectos</h1>'
    #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    engine = modelo.engine
    session = modelo.Session()
    user = Usuario()
    hashed_password = generate_password_hash(request.form['password'], method='sha256')
    user.username=request.form['username']
    user.email=request.form['email']
    user.password=hashed_password
    user.bot_token=request.form['bot_token']
    session.add(user)
    try:
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()
    return render_template('index.html')
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/descargar', methods=["POST"])
def descargar_csv():
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


def insertar_csv(fn):
    engine = modelo.engine
    conn = engine.connect()
    creader = csv.DictReader(open(fn), delimiter=',')
    for t in creader:
        d = (t['codigo'], t['nombre'], t['descripcion'], t['ciclo'], t['anno'])
        print(d)
        if d != ('', '', '', '', ''):
            conn.execute("INSERT INTO curso (codigo, nombre, descripcion, ciclo, anno) VALUES (?,?,?,?,?)", d)
    message = 'El archivo"' + fn + '" ha sido insertado exitosamente'
    print(message)
    return message


@app.route('/cargar', methods=["POST"])
@login_required
def cargar_csv():
    #Obtener nombre de archivo
    fileitem = request.files['myfile']
    # Probar si se cargo el archivo
    if fileitem.filename:
        # dejar solo el nombre del archivo para evitar ataques traversales de directorio
        fn = os.path.basename(fileitem.filename)
        archivo = open(fn, 'wb')
        archivo.write(fileitem.read())
        archivo.close()
        message = 'El archivo"' + fn + '" ha sido cargado exitosamente'
        insertar_csv(fn)
    else:
        message = 'No se ha cargado ningun archivo'
    print(message)
    return render_template('home.html')


def transformar(text_file_contents):
    return text_file_contents.replace("=", ",")


@app.route('/home', methods=['GET','post']) #Cuando el href tenga un '/home', que llegue a esta funcion y ejecute
@login_required
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
def get_cursos():
    #Ejecutar consulta y devolver datos JSON
    engine = modelo.engine
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

