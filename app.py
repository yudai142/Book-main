from flask import Flask #flask使用
from flask import render_template, request , redirect, session #htmlテンプレート機能を使用
from flask_sqlalchemy import SQLAlchemy #DB作成およびSQL操作のため

from crypt import methods #パスワードの検証
from email.policy import default #メールアドレス
from enum import unique #一意の値 usernameに使用
from venv import create
from matplotlib.pyplot import title


from flask_login import UserMixin,LoginManager, login_user,logout_user, login_required #ログイン機能
from werkzeug.security import generate_password_hash,check_password_hash #パスワードハッシュ化とチェック
import os
from flask_bootstrap import Bootstrap #ブートストラップ

from datetime import datetime #時間
import pytz #タイムゾーン設定

import requests #ISBN 書籍情報
import xml.etree.ElementTree as et 

app = Flask(__name__)
uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri and uri.startswith("postgres://"):
  uri = uri.replace("postgres://", "postgresql://", 1)
  app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['ITEMS_PER_PAGE'] = 10
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin,db.Model): #userテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique = True)
    password = db.Column(db.String(12))

class Book(db.Model): #Bookテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique = True)
    creator = db.Column(db.String(15))
    

def search_title(search_title):
    books = Book.query.filter(Book.title.like('%' + search_title + '%'))
    books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    session['title'] = search_title
    session['sort'] = ""
    return books

def sort_title(sort_value, search_title = None):
    if search_title != None:
      books = Book.query.filter(Book.title.like('%' + search_title + '%'))
      if sort_value == "asc":
        books = books.order_by(Book.title.asc())
        session['sort'] = "asc"
      elif sort_value == "desc":
        books = books.order_by(Book.title.desc())
        session['sort'] = "desc"
    else:
      if sort_value == "asc":
        books = Book.query.order_by(Book.title.asc())
        session['sort'] = "asc"
      elif sort_value == "desc":
        books = Book.query.order_by(Book.title.desc())
        session['sort'] = "desc"
    return books


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

@app.route("/", methods=['GET','POST'])
def index():
    if request.method == 'POST' and request.form.get('search-title'):
      books = search_title(request.form.get('search-title'))
      return render_template('search_results.html', books=books)
    elif request.method == 'POST' and request.form.get('sort'):
      if session['title'] != "":
        books = sort_title(request.form.get('sort'), session['title'])
        books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('search_results.html', books=books)
      else:
        books = sort_title(request.form.get('sort'))
      books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('index.html', books=books)
    else:
      session['title'] = ""
      session['sort'] = ""
      books = Book.query.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('index.html', books=books)

@app.route('/pages/<int:page_num>', methods=['GET','POST'])
def index_pages(page_num):
    if request.method == 'POST' and request.form.get('search-title'):
      books = search_title(request.form.get('search-title'))
      return render_template('search_results.html', books=books)
    elif request.method == 'POST' and request.form.get('sort'):
      books = sort_title(request.form.get('sort'))
      books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('index.html', books=books)
    else:
      if session['sort'] == "asc" or session['sort'] == "desc":
        books = sort_title(session['sort'])
      else:
        books = Book.query.paginate(page=page_num, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        return render_template('index.html', books=books)
      books = books.paginate(page=page_num, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('index.html', books=books)

@app.route('/searches/<int:page_num>', methods=['GET','POST'])
def search_pages(page_num):
    if request.method == 'POST' and request.form.get('search-title'):
      books = search_title(request.form.get('search-title'))
      return render_template('search_results.html', books=books)
    elif request.method == 'POST' and request.form.get('sort'):
      books = sort_title(request.form.get('sort'), session.get('title'))
      books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('search_results.html', books=books)
    else:
      books = sort_title(session['sort'], session.get('title'))
      books = books.paginate(page=page_num, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
      return render_template('search_results.html', books=books)

@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username = username, password = generate_password_hash(password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        title = request.form.get('title')
        creator = request.form.get('creator')
        # インスタンスを作成
        book = Book(title=title, creator=creator)
        db.session.add(book)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('create.html')

@app.route("/<int:id>/delete",methods=['GET'])
def delete(id):
    book = Book.query.get(id)

    db.session.delete(book)
    db.session.commit()
    
    return redirect('/')


@app.route('/isbn', methods=['GET', 'POST'])
def fetch_book_data():
    if request.method == 'POST':
        isbn = request.form.get('isbn')
        endpoint = 'https://iss.ndl.go.jp/api/sru'
        params = {'operation': 'searchRetrieve',
                'query': f'isbn="{isbn}"',
                'recordPacking': 'xml'}
        res = requests.get(endpoint, params=params)

        root = et.fromstring(res.text)
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        title = root.find('.//dc:title', ns).text
        creator = root.find('.//dc:creator', ns).text

        book = Book(title=title, creator=creator)
        db.session.add(book)
        db.session.commit()
        return redirect('/')

    else: 
        return render_template('isbn.html')
