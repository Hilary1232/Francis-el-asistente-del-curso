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
import cgitb
import sqlite3

from Francis.modelo import Usuario, Curso, Log, Guion

cgitb.enable()

# Crear motor para conectarse a SQLite3
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Este método se encarga de traer a un usuario de la base de datos, dado un id para identificarlo
# Retorna dicho usuario
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


# Método que simplemente redirecciona a la página para registrarse
@app.route('/register', methods=['GET'])
def register():
    return render_template('signup.html')


# Este método hace el login de un usuario dependiendo de los que este puso en los campos de nombre de usuario y contraseña
# Se hacen las verificaciones correspondientes en la base de datos para hacer un login exitoso
# Se activa o no, la opción de recordar el inicio de sesión
# Redirecciona a la página inicial index
@app.route('/login', methods=['GET', 'POST'])
def login():
    engine = modelo.engine
    session = modelo.Session()
    user = session.query(Usuario).filter_by(username=request.form['username']).first()
    if user:
        if check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form.get('remember'))
            session.commit()
            session.close()
            return redirect(url_for('home'))
    return '<h1>Usuario o contraseña incorrectos</h1>'
    # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

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
    return os.path.join('static\profile_pics', picture_fn)


# Este método es el encargado de crear una cuenta de usuario
# Recupera el nombre de usuario, la contraseña y correo para poder crearlo en la base de datos
# Se crea el ícono respectivo con la foto de usuario y su nombre, una vez que haya iniciado sesión
# Redirecciona a la página inicial index
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session = modelo.Session()
    user = Usuario()
    hashed_password = generate_password_hash(request.form['password'], method='sha256')
    user.username = request.form['username']
    validate_username(user.username)
    user.email = request.form['email']
    validate_email(user.email)
    user.password = hashed_password
    user.img_src = 'static\profile_pics\default.png'
    session.add(user)
    session.commit()
    session.close()
    flash('Su cuenta ha sido creada! Ya puede hacer login', 'success')
    return render_template('index.html')
    # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'


# Este método valida que el nombre de usuario de un usuario, sea existente para así no crear el mismo
def validate_username(username):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(username=username).first()
    session.close()
    if user:
        raise Exception('Ese usuario ya existe. Favor elegir otro.')


# Este método valida que el correo de un usuario, sea existente para así no crear el mismo
def validate_email(email):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(email=email).first()
    session.close()
    if user:
        raise Exception('Ese email ya existe. Favor elegir otro.')


# Este método se encarga de actualizar el nombre de usuario de un usuario pero sin crear uno ya existente en la base
def update_username(username):
    session = modelo.Session()
    if username != current_user.username:
        user = session.query(Usuario).filter_by(username=username).first()
        session.close()
        if user:
            raise Exception('Ese usuario ya existe. Favor elegir otro.')


# Este método se encarga de actualizar el correo de un usuario pero sin crear uno ya existente en la base
def update_email(email):
    session = modelo.Session()
    if email != current_user.email:
        user = session.query(Usuario).filter_by(email=email).first()
        session.close()
        if user:
            raise Exception('Ese email ya existe. Favor elegir otro.')


# Este método se encarga de actualizar un perfil de usuario, es decir, la cuenta del usuario
# Agarra los campos respectivos que el usuario ingresó, incluyendo la imagen, y va cambiando estos campos en la base
# Redirecciona a la página principal home
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
        print("aqui", current_user.img_src)
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


# Solo redirecciona a la página del perfil de usuario
@app.route('/profile')
def profile():
    return render_template('profile.html')


# Este método hace cierre de sesión y luego redirecciona a la página inicial index
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Este método descarga un archivo seleccionado desde la pagina presionando el botón correspondiente
# Ocupa de un archivo cargado y de aquí lo decodifica para poderlo descargar con su extensión
@app.route('/descargar', methods=["POST"])
def descargar_csv():
    request_file = request.files['myfile']
    if not request_file:
        return "No se seleccionaron archivos"

    file_contents = request_file.stream.read().decode("utf-8")

    result = transformar(file_contents)

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=" + request_file.filename
    return response


@app.route('/crear-curso', methods=["POST"])
def crear_curso():
    curso = request.form['curso']
    engine = modelo.engine
    conn = engine.connect()
    parent_dir = 'static\cursos'
    path = os.path.join(parent_dir, curso)
    # Create target Directory if don't exist
    if not os.path.exists(path):
        os.mkdir(path)
        print("Directorio ", curso, " Creado")
    else:
        print("Directorio ", curso, " ya existe")
    sql = 'INSERT INTO curso(curso) VALUES(?);'
    conn.execute(sql, curso)
    return redirect('/home')


def insertar_csv(fn):
    engine = modelo.engine
    conn = engine.connect()
    creader = csv.DictReader(open(fn), delimiter=',')
    for t in creader:
        d = (t['tema'], t['contexto'], t['respuesta'], t['sticker'], t['imagen'],  t['documento'], t['fecha_envio'])
        print(d)
        if d != ('', '', '', '', ''):
            conn.execute("INSERT INTO guion (tema, contexto, respuesta, sticker, imagen, documento, fecha_envio) VALUES (?,?,?,?,?,?,?)", d)
    message = 'El archivo"' + fn + '" ha sido insertado exitosamente'
    return message


# Este método es el encargado de cargar un archivo.csv
# Verifica si hay un archivo existente seleccionado desde la página principal utilizando el explorador de archivos , y una vez hecho esto, se carga el archivo.csv a la página
# Redirecciona a la página principal home
@app.route('/cargar', methods=["POST"])
@login_required
def cargar_csv():
    # Obtener nombre de archivo
    fileitem = request.files['myfile']
    curso = request.args.get('parameter', '')
    guiones = request.args.get('guiones', '')
    parent_dir = 'static\cursos'
    directory = os.path.join(parent_dir, curso)
    # Probar si se cargo el archivo
    if fileitem.filename:
        # dejar solo el nombre del archivo para evitar ataques traversales de directorio
        fn = os.path.basename(fileitem.filename)
        filepath = os.path.join(directory, fn)
        archivo = open(filepath, 'wb')
        archivo.write(fileitem.read())
        archivo.close()
        insertar_csv(filepath)
    flash('Guion cargado con exito!')
    return redirect('/home')


def transformar(text_file_contents):
    return text_file_contents.replace("=", ",")


@app.route('/cargar_guiones', methods=['GET', 'POST'])
@login_required
def cargar_guiones():
    curso = request.args.get('parameter', '')
    parent_dir = 'static\cursos'
    filename = os.path.join(parent_dir, curso)
    guiones = os.listdir(filename)
    return render_template("guiones.html", guiones=guiones, curso=curso)


@app.route('/home', methods=['GET', 'post'])  # Cuando el href tenga un '/home', que llegue a esta funcion y ejecute
@login_required
def home():
    parent_dir = 'static\cursos'
    cursos = os.listdir(parent_dir)
    print(cursos)
    return render_template('home.html', cursos=cursos)


# Este método recupera la key de telegram del usuario que ingresó



'''
Este método genera una tabla con todos los datos de un curso
Se seleccionatodo lo que sera visualizado en tablaCursos.html
Redirecciona a la página tablaCursos
'''


@app.route('/show-cursos', methods=['POST', 'GET'])
def tabla_cursos():
    session = modelo.Session()
    tabla = session.query(Curso)
    cursos = tabla.all()
    session.close()
    return render_template('tablaCursos.html', cursos=cursos)


'''
Este método genera una tabla con todos los datos de un log
Se seleccionatodo lo que sera visualizado en tablaLog.html
Redirecciona a la página tablaLog
'''


@app.route('/log', methods=['POST', 'GET'])
def tabla_log():
    session = modelo.Session()
    registros = session.query(Log)
    log = registros.all()
    session.close()
    return render_template('tablaLog.html', log=log)


'''
 Este método genera una tabla con todos los datos de un guion
 Se seleccionatodo lo que sera visualizado en tablaGuion.html
 Redirecciona a la página tablaGuion
'''


@app.route('/show-guiones', methods=['POST', 'GET'])
def tabla_guiones():
    session = modelo.Session()
    guiones = session.query(Guion).all()
    session.close()
    return render_template('tablaGuiones.html', guiones=guiones)


'''
Este método hace que dependiendo de los parámetros que usuario ingresó en la página de un guión, para editarlo, 
estos sean actualizados en la base de datos Esta actualización va a depender de un id ingresado para saber a cuál 
dato se está refiriendo Redirecciona a la página de guiones con los datos actualizados 
'''


@app.route('/actualizar-guion', methods=['POST', 'GET'])
def actualizar_guion():
    id = request.form['id']
    tema = request.form['tema']
    contexto = request.form['contexto']
    respuesta = request.form['respuesta']
    sticker = request.form['sticker']
    imagen = request.form['imagen']
    fecha_envio = request.form['fecha_envio']
    documento = request.form['documento']

    engine = modelo.engine
    conn = engine.connect()
    if tema != '':
        sql = 'UPDATE guion SET tema = ? WHERE id = ?;'
        conn.execute(sql, tema, id)

    if contexto != '':
        sql = 'UPDATE guion SET contexto = ? WHERE id = ?;'
        conn.execute(sql, contexto, id)

    if respuesta != '':
        sql = 'UPDATE guion SET respuesta = ? WHERE id = ?;'
        conn.execute(sql, respuesta, id)

    if sticker != '':
        sql = 'UPDATE guion SET sticker = ? WHERE id = ?;'
        conn.execute(sql, sticker, id)

    if imagen != '':
        sql = 'UPDATE guion SET imagen = ? WHERE id = ?;'
        conn.execute(sql, imagen, id)

    if fecha_envio == 'Kill':
        kill = ''
        sql = 'UPDATE guion SET fecha_envio = ? WHERE id = ?;'
        conn.execute(sql, kill, id)

    if fecha_envio != '':
        sql = 'UPDATE guion SET fecha_envio = ? WHERE id = ?;'
        conn.execute(sql, fecha_envio, id)

    if documento != '' and documento is not None:
        sql = 'UPDATE guion SET documento = ? WHERE id = ?;'
        conn.execute(sql, documento, id)

    conn.close()
    session = modelo.Session()
    data = session.query(Guion)
    guiones = data.all()
    session.close()
    return render_template('tablaGuiones.html', guiones=guiones)


app.run(host='localhost', port=5001, debug=True)
