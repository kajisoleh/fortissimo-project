import os
from os.path import join, dirname
from bson import ObjectId
import bson
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"

SECRET_KEY = "CORSAIR"


app = Flask(__name__)


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
    return render_template('index.html', user_info=user_info)

@app.route('/admin')
def admin():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        if user_info["role"] == "admin":
            return render_template('admin/index.html', user_info=user_info)
        else:
            return redirect(url_for("home"))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))
    
@app.route('/register-admin', methods=["GET"])
def register_admin():
    return render_template("admin/tambah-admin.html")

@app.route("/register-admin/save", methods=["POST"])
def register_admin_save():
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
        daftar_items = list(db.daftar.find({}))
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
        daftar_items = list(db.daftar.find({}))
        return render_template('admin/data-peserta.html', user_info=user_info, daftar_items=daftar_items)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was problem logging you in"))
    
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
    print (data)
    return render_template("admin/edit-peserta.html", data=data)
    
@app.route('/user-data', methods=['GET'])
def data_user():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"username": payload["id"]})
        user_items = list(db.users.find({}))
        no = 1
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
    return render_template("admin/create-pendaftar.html")

@app.route('/daftar-admin-form/save', methods=['POST'])
def save_daftar_admin():
    nama = request.form['nama_give']
    alamat = request.form['alamat_give']
    email = request.form['email_give']
    nohp = request.form['nohp_give']
    instrumen = request.form['instrumen_give']
    umur = request.form['umur_give']

    daftar_id = db.daftar.insert_one({
        'nama': nama,
        'alamat': alamat,
        'email': email,
        'nohp': nohp,
        'instrumen': instrumen,
        'umur': umur,
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
    return render_template('user/about.html')

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
        'status': 'pending'
    }).inserted_id

    return jsonify({'status': 'success', 'msg': 'Proses pendaftaran berhasil, silahkan tunggu.', 'daftar_id': str(daftar_id)})

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)