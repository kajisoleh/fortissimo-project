import os
from os.path import join, dirname
import smtplib
from bson import ObjectId
import bson
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, flash, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask_paginate import Pagination, get_page_args
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging


logging.basicConfig(level=logging.DEBUG)


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"
app.secret_key = 'fortissimo'
MAIL_USERNAME = 'fortissimocourse@gmail.com'
MAIL_PASSWORD = 'pqut hlpz brdo wwuz'  # Pastikan ini adalah kata sandi yang benar atau kata sandi aplikasi
SECRET_KEY = "CORSAIR"



def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(MAIL_USERNAME, to_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/')
def home():
    token_receive = request.cookies.get("mytoken")
    user_info = None
    if token_receive:
        print(user_info)
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"username": payload["id"]})
            if user_info and user_info.get("role") == "admin":
                return redirect(url_for("admin"))
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login", msg="Your token has expired"))
        except jwt.exceptions.DecodeError:
            return redirect(url_for("login", msg="There was problem logging you in"))
    testimoni_data = list(db.testimoni.find({}))
    return render_template('index.html', user_info=user_info, testimoni_data=testimoni_data)

@app.route('/admin')
def admin():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        daftar_items = list(db.daftar.find({}))
        jumlah_pendaftar = db.daftar.count_documents({"status": "pending"})
        jumlah_siswa = db.daftar.count_documents({"status": "Approve"})
        search_query = request.args.get('search', '')
        
        # Menerapkan filter pencarian jika ada
        if search_query:
            daftar_items = db.daftar.find({"nama": {"$regex": search_query, "$options": "i"}})
        else:
            daftar_items = db.daftar.find({})
        if user_info["role"] == "admin":
            return render_template('admin/index.html', user_info=user_info, daftar_items=daftar_items, jumlah_pendaftar=jumlah_pendaftar, jumlah_siswa=jumlah_siswa)
        else:
            return redirect(url_for("home"))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))
    
@app.route('/register-admin', methods=["GET"])
def register_admin():
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    user_info = db.users.find_one({"username": payload["id"]})
    return render_template("admin/tambah-admin.html", user_info=user_info)

@app.route("/register-admin/save", methods=["POST"])
def register_admin_save():
    email_receive = request.form['email_give']
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    existing_user = db.users.find_one({"email": email_receive})
    if existing_user:
        return jsonify({'exists': 'Email already exists in the database. Please use a different email.'}), 400
    doc = {
        "email": email_receive,
        "username": username_receive,                               # id
        "password": password_hash,                                  # password
        "profile_name": username_receive,                           # user's name is set to their id by default
        "profile_pic": "",                                          # profile image file name
        "profile_pic_real": "profile_pics/profile_placeholder.png", # a default profile image
        "profile_info": "",                                          # a profile description
        "role": "admin"
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/pendaftar', methods=['GET'])
def pendaftar():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        search_query = request.args.get('search', '')

        # Terapkan filter pencarian jika ada
        if search_query:
            filter_query = {
            "$or": [
                {"nama": {"$regex": search_query, "$options": "i"}},
                {"alamat": {"$regex": search_query, "$options": "i"}},
                {"instrumen": {"$regex": search_query, "$options": "i"}},
                {"price_list": {"$regex": search_query, "$options": "i"}},
            ]
        }
        else:
            filter_query = {}
        daftar_items = list(db.daftar.find(filter_query))
        return render_template('admin/data-pendaftar.html', user_info=user_info, daftar_items=daftar_items)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))
    
@app.route('/pendaftar-update/<id>', methods=['POST'])
def pendaftar_update(id):
    doc = {'status': 'Approve'}
    db.daftar.update_one({'_id': ObjectId(id)}, {"$set": doc})
    return redirect(url_for('pendaftar'))

@app.route('/peserta', methods=['GET'])
def peserta():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})

        search_query = request.args.get('search', '')

        # Terapkan filter pencarian jika ada
        if search_query:
            filter_query = {
                "$or": [
                    {"nama": {"$regex": search_query, "$options": "i"}},
                    {"alamat": {"$regex": search_query, "$options": "i"}},
                    {"instrumen": {"$regex": search_query, "$options": "i"}}
                ]
            }
        else:
            filter_query = {}

        # Parameter paginasi
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page',default_per_page=2)

        # Kueri untuk data yang dipaginasi
        daftar_items_cursor = db.daftar.find(filter_query).skip(offset).limit(per_page)
        daftar_items = list(daftar_items_cursor)

        # Hitung total dokumen (termasuk filter)
        total = db.daftar.count_documents(filter_query)

        # Objek paginasi
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

        return render_template('admin/data-peserta.html', user_info=user_info, daftar_items=daftar_items, pagination=pagination)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was a problem logging you in"))
    
@app.route('/edit-peserta/<string:_id>', methods=['GET', 'POST'])
def edit_admin_peserta(_id):
    if request.method=='POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        email = request.form['email']
        nohp = request.form['nohp']
        instrumen = request.form['instrumen']
        umur = request.form['umur']

        doc = {
            'nama': nama,
            'alamat': alamat,
            'email': email,
            'nohp': nohp,
            'instrumen': instrumen,
            'umur': umur
        }

        db.daftar.update_one({'_id': ObjectId(_id)}, {"$set": doc})
        return redirect(url_for("peserta"))

    id = ObjectId(_id)
    data = list(db.daftar.find({'_id': id}))
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    user_info = db.users.find_one({"username": payload["id"]})
    print (data)
    return render_template("admin/edit-peserta.html", data=data, user_info=user_info)
    
@app.route('/user-data', methods=['GET'])
def data_user():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        no = 1
        search_query = request.args.get('search', '')

        # Terapkan filter pencarian jika ada
        if search_query:
            filter_query = {"profile_name": {"$regex": search_query, "$options": "i"}}
        else:
            filter_query = {}
        user_items = list(db.users.find(filter_query))
        return render_template('admin/data-user.html', user_info=user_info, user_items=user_items)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))
    
@app.route("/profile-admin/<id>")
def profile_admin(id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_id = ObjectId(id)
        status = str(payload["id"]) == id
        user_info = db.users.find_one({"_id": user_id})
        if user_info:
            daftar_list = list(db.daftar.find({"user_id": user_id}))
            print(daftar_list)
            return render_template("admin/profile.html", user_info=user_info, status=status)
        else:
            return "User not found"

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError, bson.errors.InvalidId):
        return redirect(url_for("home"))
    
@app.route('/edit-admin/<string:_id>', methods=['GET', 'POST'])
def edit_admin(_id):
    if request.method=='POST':
        profile_name = request.form['profile_name']
        email = request.form['email']
        nama_gambar = request.files['profile_pic_real']

        doc = {
            'profile_name': profile_name,
            'email': email
        }

        if nama_gambar:
            nama_file_asli = nama_gambar.filename
            nama_file_gambar = nama_file_asli.split('/')[-1]
            file_path = f'static/profile_pics/{nama_file_gambar}'
            nama_gambar.save(file_path)
            doc['profile_pic_real'] = f'profile_pics/{nama_file_gambar}'

        db.users.update_one({'_id': ObjectId(_id)}, {"$set": doc})
        return redirect(url_for("profile_admin", id=_id))

    user_info = db.users.find_one({'_id': ObjectId(_id)})
    id = ObjectId(_id)
    data = list(db.users.find({'_id': id}))
    print (data)
    return render_template("admin/edit.html", data=data, user_info=user_info)

@app.route('/form-daftar-admin')
def pendaftar_admin():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        daftar_items = list(db.daftar.find({}))
        return render_template('admin/create-pendaftar.html', user_info=user_info, daftar_items=daftar_items)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))

@app.route('/daftar-admin-form/save', methods=['POST'])
def save_daftar_admin():
    nama = request.form.get('nama_give')
    alamat = request.form.get('alamat_give')
    email = request.form.get('email_give')
    nohp = request.form.get('nohp_give')
    instrumen = request.form.get('instrumen_give')
    umur = request.form.get('umur_give')
    price_list = request.form.get('list_give')

    # Validasi jika ada data yang kosong
    if not all([nama, alamat, email, nohp, instrumen, umur]):
        # Data ada yang kosong, tampilkan pesan gagal dan redirect kembali ke halaman sebelumnya
        return jsonify({'status': 'error', 'msg': 'Gagal! Silahkan lengkapi semua data.'})

    # Semua data sudah diisi, lanjutkan dengan proses pendaftaran
    daftar_id = db.daftar.insert_one({
        'nama': nama,
        'alamat': alamat,
        'email': email,
        'nohp': nohp,
        'instrumen': instrumen,
        'umur': umur,
        'price_list': price_list,
        'status': 'pending'
    })

    return jsonify({'status': 'success', 'msg': 'Proses pendaftaran berhasil, silahkan tunggu.'})


@app.route('/delete/admin/<string:_id>', methods=['POST'])
def hapus_admin_user(_id):
    id = ObjectId(_id)
    db.users.delete_one({'_id': id})
    return jsonify({'status': 'success', 'msg': 'Data user berhasil di hapus '})

@app.route('/delete/admin-peserta/<string:_id>', methods=['POST'])
def hapus_admin_peserta(_id):
    id = ObjectId(_id)
    db.daftar.delete_one({'_id': id})
    return jsonify({'status': 'success', 'msg': 'Data user berhasil di hapus '})


@app.route('/delete/user/<string:_id>', methods=['POST'])
def hapus_user(_id):
    id = ObjectId(_id)
    db.users.delete_one({'_id': id})
    return jsonify({'status': 'success', 'msg': 'Data user berhasil di hapus '})

@app.route('/login', methods=['GET'])
def login():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)


@app.route('/login/save', methods=['POST'])
def login_save():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": username_receive,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )

@app.route('/register', methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/register/save", methods=["POST"])
def register_save():
    email_receive = request.form['email_give']
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    existing_user = db.users.find_one({"email": email_receive})
    if existing_user:
        return jsonify({'error': 'Email already exists in the database. Please use a different email.'}), 400
    doc = {
        "email": email_receive,
        "username": username_receive,                               # id
        "password": password_hash,                                  # password
        "profile_name": username_receive,                           # user's name is set to their id by default
        "profile_pic": "",                                          # profile image file name
        "profile_pic_real": "profile_pics/profile_placeholder.png", # a default profile image
        "profile_info": "",                                          # a profile description
        "role": "user"
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/about', methods=['GET'])
def about():
    token_receive = request.cookies.get("mytoken")
    user_info = None
    if token_receive:
        print(user_info)
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"username": payload["id"]})
            if user_info and user_info.get("role") == "admin":
                return redirect(url_for("admin"))
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login", msg="Your token has expired"))
        except jwt.exceptions.DecodeError:
            return redirect(url_for("login", msg="There was problem logging you in"))
    return render_template('user/about.html', user_info=user_info)

@app.route("/profile/<id>")
def profile(id):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_id = ObjectId(id)
        status = str(payload["id"]) == id
        user_info = db.users.find_one({"_id": user_id})
        if user_info:
            daftar_list = list(db.daftar.find({"user_id": user_id}))
            print(daftar_list)
            return render_template("user/profile.html", user_info=user_info, daftar_list=daftar_list, status=status)
        else:
            return "User not found"

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError, bson.errors.InvalidId):
        return redirect(url_for("home"))

@app.route('/edit/<string:_id>', methods=['GET', 'POST'])
def edit(_id):
    if request.method=='POST':
        profile_name = request.form['profile_name']
        email = request.form['email']
        nama_gambar = request.files['profile_pic_real']

        doc = {
            'profile_name': profile_name,
            'email': email
        }

        if nama_gambar:
            nama_file_asli = nama_gambar.filename
            nama_file_gambar = nama_file_asli.split('/')[-1]
            file_path = f'static/profile_pics/{nama_file_gambar}'
            nama_gambar.save(file_path)
            doc['profile_pic_real'] = f'profile_pics/{nama_file_gambar}'

        db.users.update_one({'_id': ObjectId(_id)}, {"$set": doc})
        return redirect(url_for("profile", id=_id))

    user_info = db.users.find_one({'_id': ObjectId(_id)})
    id = ObjectId(_id)
    data = list(db.users.find({'_id': id}))
    print (data)
    return render_template("user/edit.html", data=data, user_info=user_info)

@app.route('/daftar/<username>', methods=['GET'])
def daftar(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        status = username == payload["id"]

        user_info = db.users.find_one({"username": username}, {"_id": False})

        return render_template("user/form-daftar.html", user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
    
@app.route('/daftar/save', methods=['POST'])
def save_daftar():
    nama = request.form['nama_give']
    alamat = request.form['alamat_give']
    email = request.form['email_give']
    nohp = request.form['nohp_give']
    instrumen = request.form['instrumen_give']
    umur = request.form['umur_give']
    list_price = request.form['list_give']

    user = db.users.find_one({'email': email})

    user_id = user['_id']

    daftar_id = db.daftar.insert_one({
        'user_id': user_id,
        'nama': nama,
        'alamat': alamat,
        'email': email,
        'nohp': nohp,
        'instrumen': instrumen,
        'umur': umur,
        'price_list': list_price,
        'status': 'pending'
    }).inserted_id

    return jsonify({'status': 'success', 'msg': 'Proses pendaftaran berhasil, silahkan tunggu.', 'daftar_id': str(daftar_id)})

@app.route('/testimoni/save', methods=['POST'])
def testimoni_save():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for('login'))  # Redirect ke halaman login jika tidak ada token

    logging.debug("Token received: %s", token_receive)
    user = db.users.find_one({})
    user_id = user['_id']
    testimoni = request.form['testimoni_give']
    nama = request.form['nama_give']
    email = request.form['email_give']
    subject = request.form['subject_give']

    

    if not testimoni:
        return jsonify({'msg': 'Testimoni cannot be empty'}), 400

    doc = {
        'user_id': user_id,
        'testimoni': testimoni,
        'nama': nama,
        'email': email,
        'subject': subject,
    }

    try:
        db.testimoni.insert_one(doc)
        return jsonify({'msg': 'Terima kasih atas pengisian testimoninya '})
    except Exception as e:
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = db.users.find_one({'email': email})
        if user:
            token = jwt.encode({'email': email, 'exp': datetime.now(timezone.utc) + timedelta(minutes=30)}, SECRET_KEY, algorithm='HS256')
            reset_url = url_for('reset_with_token', token=token, _external=True)
            subject = "Password Reset Request"
            body = f'Please click the following link to reset your password: {reset_url}'
            send_email(email, subject, body)
            return render_template('email_sent.html')
        else:
            flash('Email address not found', 'error')
    return render_template('reset_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        email = data['email']
    except jwt.ExpiredSignatureError:
        flash('Tautan reset telah kedaluwarsa', 'error')
        return redirect(url_for('reset_password'))
    except jwt.InvalidTokenError:
        flash('Tautan reset tidak valid', 'error')
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        new_password = request.form['password']

        hashed_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        db.users.update_one({'email': email}, {'$set': {'password': hashed_password}})
        flash('Kata sandi Anda telah diperbarui!', 'success')
        return redirect(url_for('login'))

    return render_template('new_password.html', token=token)



if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)