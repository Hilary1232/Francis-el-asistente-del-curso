#!/usr/bin/python
from flask_restful import Resource, Api
from flask import Flask, render_template, redirect, url_for, make_response, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
import modelo
import csv
import os
import secrets
import cgitb
from modelo import Usuario, Curso, Log, Guion, Grupo

cgitb.enable()

# Crear motor para conectarse a SQLite3
app = Flask(__name__)
api = Api(app)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Este metodo se encarga de traer a un usuario de la base de datos, dado un id para identificarlo
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


# Metodo que simplemente redirecciona a la pagina para registrarse
@app.route('/register', methods=['GET'])
def register():
    return render_template('signup.html')


# Este metodo hace el login de un usuario dependiendo de los que este puso en los campos de nombre de usuario y contrasena
# Se hacen las verificaciones correspondientes en la base de datos para hacer un login exitoso
# Se activa o no, la opcion de recordar el inicio de sesion
# Redirecciona a la pagina inicial index
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
    return '<h1>Usuario o contrasenna incorrectos</h1>'
    # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('index.html')


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    print(picture_fn)
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    archivo = open(picture_path, 'wb')
    archivo.write(form_picture.read())
    archivo.close()
    return os.path.join('static/profile_pics', picture_fn)


# Este metodo es el encargado de crear una cuenta de usuario
# Recupera el nombre de usuario, la contrasenna y correo para poder crearlo en la base de datos
# Se crea el icono respectivo con la foto de usuario y su nombre, una vez que haya iniciado sesion
# Redirecciona a la pagina inicial index
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
    user.img_src = 'static/profile_pics/default.png'
    session.add(user)
    session.commit()
    session.close()
    flash('Su cuenta ha sido creada! Ya puede hacer login', 'success')
    return render_template('index.html')
    # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'


# Este metodo valida que el nombre de usuario de un usuario, sea existente para asi no crear el mismo
def validate_username(username):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(username=username).first()
    session.close()
    if user:
        raise Exception('Ese usuario ya existe. Favor elegir otro.')


# Este metodo valida que el correo de un usuario, sea existente para asi no crear el mismo
def validate_email(email):
    session = modelo.Session()
    user = session.query(Usuario).filter_by(email=email).first()
    session.close()
    if user:
        raise Exception('Ese email ya existe. Favor elegir otro.')

# Este metodo se encarga de actualizar el nombre de usuario de un usuario pero sin crear uno ya existente en la base
def update_username(username):
    session = modelo.Session()
    if username != current_user.username:
        user = session.query(Usuario).filter_by(username=username).first()
        session.close()
        if user:
            raise Exception('Ese usuario ya existe. Favor elegir otro.')


# Este metodo se encarga de actualizar el correo de un usuario pero sin crear uno ya existente en la base
def update_email(email):
    session = modelo.Session()
    if email != current_user.email:
        user = session.query(Usuario).filter_by(email=email).first()
        session.close()
        if user:
            raise Exception('Ese email ya existe. Favor elegir otro.')


# Este metodo se encarga de actualizar un perfil de usuario, es decir, la cuenta del usuario
# Agarra los campos respectivos que el usuario ingreso, incluyendo la imagen, y va cambiando estos campos en la base
# Redirecciona a la pagina principal home
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


# Solo redirecciona a la pagina del perfil de usuario
@app.route('/profile')
def profile():
    return render_template('profile.html')


# Este metodo hace cierre de sesion y luego redirecciona a la pagina inicial index
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Este metodo descarga un archivo seleccionado desde la pagina presionando el boton correspondiente
# Ocupa de un archivo cargado y de aqui lo decodifica para poderlo descargar con su extension
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
    parent_dir = 'static/cursos'
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
        d = (t['tema'], t['contexto'], t['respuesta'], t['sticker'], t['imagen'],  t['documento'],t['grupo_id'], t['fecha_envio'])
        print(d)
        if d != ('', '', '', '', '','','',''):
            conn.execute("INSERT INTO guion (tema, contexto, respuesta, sticker, imagen, documento, grupo_id, fecha_envio) VALUES (?,?,?,?,?,?,?,?)", d)
    message = 'El archivo"' + fn + '" ha sido insertado exitosamente'
    return message


# Este metodo es el encargado de cargar un archivo.csv
# Verifica si hay un archivo existente seleccionado desde la pagina principal utilizando el explorador de archivos , y una vez hecho esto, se carga el archivo.csv a la pagina
# Redirecciona a la pagina principal home
@app.route('/cargar', methods=["POST"])
@login_required
def cargar_csv():
    # Obtener nombre de archivo
    fileitem = request.files['myfile']
    curso = request.args.get('parameter', '')
    guiones = request.args.get('guiones', '')
    parent_dir = 'static/cursos'
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


@app.route('/imagenes', methods=['GET','POST'])
def imagenes():
    imgs = os.listdir('static/img')
    return render_template('imagenes.html', imgs=imgs)

@app.route('/subir-imagen', methods=['GET','POST'])
def subir_imagen():
    fileitem = request.files['myfile']
    fn = os.path.basename(fileitem.filename)
    directory='static/img'
    filepath = os.path.join(directory, fn)
    archivo = open(filepath, 'wb')
    archivo.write(fileitem.read())
    archivo.close()
    return redirect('/imagenes')


@app.route('/documentos', methods=['GET','POST'])
def documentos():
    docs = os.listdir('static/files')
    return render_template('documentos.html', docs=docs)


@app.route('/subir-doc', methods=['GET','POST'])
def subir_doc():
    fileitem = request.files['myfile']
    fn = os.path.basename(fileitem.filename)
    directory = 'static/files'
    filepath = os.path.join(directory, fn)
    archivo = open(filepath, 'wb')
    archivo.write(fileitem.read())
    archivo.close()
    return redirect('/documentos')


@app.route('/stickers', methods=['GET','POST'])
def stickers():
    stickers = os.listdir('static/stickers')
    return render_template('stickers.html', stickers=stickers)


@app.route('/subir-sticker', methods=['GET','POST'])
def subir_sticker():
    fileitem = request.files['myfile']
    fn = os.path.basename(fileitem.filename)
    directory = 'static/stickers'
    filepath = os.path.join(directory, fn)
    archivo = open(filepath, 'wb')
    archivo.write(fileitem.read())
    archivo.close()
    return redirect('/stickers')



@app.route('/cargar_guiones', methods=['GET', 'POST'])
@login_required
def cargar_guiones():
    curso = request.args.get('parameter', '')
    parent_dir = 'static/cursos'
    filename = os.path.join(parent_dir, curso)
    guiones = os.listdir(filename)
    return render_template("guiones.html", guiones=guiones, curso=curso)


@app.route('/home', methods=['GET', 'post'])  # Cuando el href tenga un '/home', que llegue a esta funcion y ejecute
@login_required
def home():
    parent_dir = 'static/cursos'
    cursos = os.listdir(parent_dir)
    print(cursos)
    return render_template('home.html', cursos=cursos)


# Este metodo recupera la key de telegram del usuario que ingreso



'''
Este metodo genera una tabla con todos los datos de un curso
Se seleccionatodo lo que sera visualizado en tablaCursos.html
Redirecciona a la pagina tablaCursos
'''


@app.route('/show-cursos', methods=['POST', 'GET'])
def tabla_cursos():
    session = modelo.Session()
    tabla = session.query(Curso)
    cursos = tabla.all()
    session.close()
    return render_template('tablaCursos.html', cursos=cursos)


'''
Este metodo genera una tabla con todos los datos de un log
Se seleccionatodo lo que sera visualizado en tablaLog.html
Redirecciona a la pagina tablaLog
'''


@app.route('/log', methods=['POST', 'GET'])
def tabla_log():
    session = modelo.Session()
    registros = session.query(Log)
    log = registros.all()
    session.close()
    return render_template('tablaLog.html', log=log)


'''
 Este metodo genera una tabla con todos los datos de un guion
 Se seleccionatodo lo que sera visualizado en tablaGuion.html
 Redirecciona a la pagina tablaGuion
'''
@app.route('/webhook',methods=['POST','GET'])
def webhook():
    dir = request.form['url']
    urld = 'https://api.telegram.org/bot1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ/setWebHook?url='
    url = urld.strip() + dir.strip()
    return redirect(url)


@app.route('/show-guiones', methods=['POST', 'GET'])
def tabla_guiones():
    session = modelo.Session()
    guiones = session.query(Guion).all()
    session.close()
    return render_template('tablaGuiones.html', guiones=guiones)

@app.route('/grupos', methods=['POST', 'GET'])
def grupos():
    session = modelo.Session()
    grupos = session.query(Grupo).all()
    session.close()
    return render_template('grupos.html', grupos=grupos)

'''
Este metodo hace que dependiendo de los parametros que usuario ingreso en la pagina de un guion, para editarlo, 
estos sean actualizados en la base de datos Esta actualizacion va a depender de un id ingresado para saber a cual 
dato se esta refiriendo Redirecciona a la pagina de guiones con los datos actualizados 
Esto pasa al igual que con la opcion de eliminar, que se borra un guion en la base, y al igual con crear, que crea un guion en la base
'''
@app.route('/guiones', methods=['POST', 'GET'])
def actualizar_guion():
    id = request.form['id']
    tema = request.form['tema']
    contexto = request.form['contexto']
    respuesta = request.form['respuesta']
    sticker = request.form['sticker']
    imagen = request.form['imagen']
    fecha_envio = request.form['fecha_envio']
    documento = request.form['documento']
    grupo_id = request.form['grupo_id']
    boton = request.form["bsubmit"]

    engine = modelo.engine
    conn = engine.connect()

    if(boton == "Actualizar Registro"):
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

        if grupo_id != '' and documento is not None:
            sql = 'UPDATE guion SET grupo_id = ? WHERE id = ?;'
            conn.execute(sql, grupo_id, id)

    if (boton == "Crear Registro"):
        sql = 'INSERT INTO guion (tema,contexto,respuesta,sticker,imagen,documento,grupo_id,fecha_envio) VALUES (?,?,?,?,?,?,?,?);'
        conn.execute(sql, tema, contexto, respuesta, sticker, imagen, documento, grupo_id,fecha_envio)

    if (boton == "Borrar Registro"):
        sql = 'DELETE FROM guion WHERE id = ?;'
        conn.execute(sql, id)


    conn.close()
    session = modelo.Session()
    data = session.query(Guion)
    guiones = data.all()
    session.close()
    return render_template('tablaGuiones.html', guiones=guiones)

'''
Este metodo hace que dependiendo de los parametros que usuario ingreso en la pagina de un curso, para editarlo, 
estos sean actualizados en la base de datos, esta actualizacion va a depender de un id ingresado para saber a cual 
dato se esta refiriendo, redirecciona a la pagina de cursos con los datos actualizados
Esto pasa al igual que con la opcion de eliminar, que se borra un curso en la base, y al igual con crear, que crea un curso en la base
'''
@app.route('/cursos', methods=['POST', 'GET'])
def crud_cursos():
    id = request.form['id']
    nombre = request.form['nombre']
    boton = request.form["bsubmit"]

    engine = modelo.engine
    conn = engine.connect()

    if(boton == "Actualizar Curso"):
        if(nombre != '' and nombre is not None):
            sql = 'UPDATE curso SET curso = ? WHERE id = ?;'
            conn.execute(sql, nombre, id)

    if (boton == "Crear Curso"):
        sql = 'INSERT INTO curso (curso) VALUES(?);'
        conn.execute(sql, nombre)

    if (boton == "Borrar Curso"):
        sql = 'DELETE FROM curso WHERE id = ?;'
        conn.execute(sql, id)

    conn.close()
    session = modelo.Session()
    data = session.query(Curso)
    cursos = data.all()
    session.close()
    return render_template('tablaCursos.html', cursos=cursos)

app.run(host='localhost', port=5001, debug=True)
