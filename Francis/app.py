from flask_restful import Resource, Api
from flask import Flask, render_template, redirect, url_for, make_response, request, flash
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import modelo
import csv
import json
import collections
import os
import secrets
from PIL import Image
import cgitb;cgitb.enable()
from Francis.modelo import Usuario


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
    user = session.query(Usuario).get(int(user_id))
    session.close()
    return user


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
    user = session.query(Usuario).first()
    if user:
        if check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            session.commit()
            session.close()
            return redirect(url_for('home'))

    return '<h1>Usuario o contraseña incorrectos</h1>'
    #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('index.html')


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    print(picture_fn)
    picture_path = os.path.join(app.root_path, 'static\profile_pics', picture_fn)
    archivo = open(picture_path, 'wb')
    archivo.write(form_picture.read())
    archivo.close()
    return os.path.join('static\profile_pics',picture_fn)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session = modelo.Session()
    user = Usuario()
    hashed_password = generate_password_hash(request.form['password'], method='sha256')
    user.username=request.form['username']
    validate_username(user.username)
    user.email=request.form['email']
    validate_email(user.email)
    user.password=hashed_password
    user.bot_token=request.form['bot_token']
    user.img_src = 'static\profile_pics\default.png'
    session.add(user)
    try:
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()
    flash('Su cuenta ha sido creada! Ya puede hacer login', 'success')
    return render_template('index.html')
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

def validate_username(username):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(username=username).first()
    session.close()
    if user:
        raise Exception('Ese usuario ya existe. Favor elegir otro.')


def validate_email(email):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(email).first()
    session.close()
    if user:
        raise Exception('Ese email ya existe. Favor elegir otro.')


def update_username(username):
    session = modelo.Session()
    if username!= current_user.username:
        user = session.query(Usuario).filter_by(username=username).first()
        session.close()
        if user:
            raise Exception('Ese usuario ya existe. Favor elegir otro.')


def update_email(email):
    session = modelo.Session()
    if email!= current_user.email:
        user = session.query(Usuario).filter_by(email=email).first()
        session.close()
        if user:
            raise Exception('Ese email ya existe. Favor elegir otro.')


@app.route("/account", methods=['GET', 'POST'])
@login_required
def update_account():
    engine = modelo.engine
    conn = engine.connect()
    session = modelo.Session()
    fileitem = request.files['img']
    if fileitem.filename:
        picture_file = save_picture(fileitem)
        current_user.img_src = picture_file
        print("aqui",current_user.img_src)
    current_user.username = request.form['username']
    update_username(current_user.username)
    current_user.email = request.form['email']
    update_email(current_user.email)
    sql = ''' UPDATE usuario
              SET email = ? ,
                  username = ? ,
                  img_src = ?
              WHERE id = ?'''
    task = (current_user.email, current_user.username, current_user.img_src, current_user.id)
    conn.execute(sql, task)
    session.commit()
    flash('Su perfil ha sido actualizado!', 'success')
    return render_template('home.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')



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
    engine = modelo.engine
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
    print(app.root_path)
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

