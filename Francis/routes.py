import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, make_response
from Francis import app, db, bcrypt
from Francis.forms import RegistrationForm, LoginForm, UpdateAccountForm
from Francis.models import User
from flask_login import login_user, current_user, logout_user, login_required
import collections
import json


@app.route('/', methods=['GET'])  # Cuando el href solo tenga un '/', que llegue a esta funcion y ejecute
def index():
    return render_template('index.html')


@app.route('/home', methods=['GET', 'post'])  # Cuando el href tenga un '/home', que llegue a esta funcion y ejecute
def home():
    return render_template('home.html')


@app.route('/cursos', methods=['GET'])  # Cuando la solicitud tiene un /cursos, devuelva la pagina de cursos
def cursos():
    return render_template('cursos.html')


@app.route('/get-key', methods=['POST'])
def get_key():
    bot_key = request.form['key']
    # key = 1043017404:AAEZabTKNCf8csRbBVvNljrRZ8INL520ZLQ


@app.route('/cursos-get')  # Es llamada por Javascript, para mostrar la tabla de cursos de la base.
def getcursos():
    # Ejecutar consulta y devolver datos JSON
    conn = db.connect()
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

@app.route('/descargar', methods=["POST"])
def descargar_archivo_csv():
    request_file = request.files['data_file']
    if not request_file:
        return "No se seleccionó ningún archivo"

    file_contents = request_file.stream.read().decode("utf-8")

    result = transformar(file_contents)

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=FRANCIS_CSV_FILE.csv"
    return response


def transformar(text_file_contents):
    return text_file_contents.replace("=", ",")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Su cuenta ha sido creada! Ya puede hacer login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login exitoso. Revisar usuario contraseña', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Su perfil ha sido actualizado!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)
