from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
import configparser
import time
from flask import send_from_directory

app = Flask(__name__)
# ログインが必要なデコレータを作成
def login_required(func):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash('ログインが必要です')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# データベースファイルをダウンロードするためのエンドポイント
@app.route('/download_db')
@login_required  # ログインが必要なエンドポイント
def download_db():
    db_path = '/persistent'  # データベースファイルが格納されているディレクトリ
    return send_from_directory(db_path, 'todo.db', as_attachment=True)

# データベースファイルをアップロードして適用するためのエンドポイント
@app.route('/upload_db', methods=['GET', 'POST'])
@login_required  # ログインが必要なエンドポイント
def upload_db():
    if request.method == 'POST':
        if 'db_file' not in request.files:
            return "No file part", 400
        file = request.files['db_file']
        if file.filename == '':
            return "No selected file", 400
        if file:
            file_path = '/persistent/todo.db'
            file.save(file_path)
            return "Database uploaded and replaced successfully!", 200
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="db_file">
        <input type="submit" value="Upload">
    </form>
    '''

# データベースファイルを削除するためのエンドポイント
@app.route('/delete_db', methods=['POST'])
@login_required  # ログインが必要なエンドポイント
def delete_db():
    db_path = '/persistent/todo.db'
    try:
        if os.path.exists(db_path):
            os.remove(db_path)  # データベースファイルを削除
            return "Database deleted successfully!", 200
        else:
            return "Database file not found.", 404
    except Exception as e:
        return f"An error occurred while deleting the database: {e}", 500


# config.ini から設定を読み込む
config = configparser.ConfigParser()
config.read('config.ini')

# IDとパスワード、シークレットキーを設定ファイルから取得
USER_ID = config['DEFAULT'].get('USER_ID', 'admin')
PASSWORD = config['DEFAULT'].get('PASSWORD', '1111')
app.secret_key = config['DEFAULT'].get('SECRET_KEY', 'your_secret_key')

# 永続ディスクのマウントポイント
PERSISTENT_DIR = '/persistent'

# 永続ディスクディレクトリが存在しない場合は作成
if not os.path.exists(PERSISTENT_DIR):
    try:
        os.makedirs(PERSISTENT_DIR)
    except OSError as e:
        app.logger.error(f'ディレクトリの作成に失敗しました: {e}')
        raise

# データベースの設定（永続ディスクにSQLiteを保存）
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{PERSISTENT_DIR}/todo.db'
db = SQLAlchemy(app)

# モデルの定義
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    order = db.Column(db.Integer, nullable=False, default=0)
    tasks = db.relationship('Task', backref='person', lazy=True, order_by='Task.priority')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Date, nullable=True)  # 期限フィールドを追加
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)

# 初期データの作成
def create_initial_data():
    if not Person.query.first():
        person_a = Person(name='Aさん', order=0)
        person_b = Person(name='Bさん', order=1)
        db.session.add_all([person_a, person_b])
        db.session.commit()

# テーブル作成（初回起動時のみ）
with app.app_context():
    db.create_all()
    create_initial_data()

# ログイン試行回数とタイムスタンプを保存する辞書
login_attempts = {}

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_user_id = request.form['user_id']
        input_password = request.form['password']
        current_time = time.time()

        # 試行回数と最初の試行時間の初期化
        if input_user_id not in login_attempts:
            login_attempts[input_user_id] = {'count': 0, 'first_attempt_time': current_time}

        # 試行回数が3回を超えた場合のチェック
        attempts_info = login_attempts[input_user_id]
        if attempts_info['count'] >= 3:
            time_diff = current_time - attempts_info['first_attempt_time']
            if time_diff < 3600:
                flash('ログイン試行回数が制限を超えました。1時間後に再度お試しください。')
                return redirect(url_for('login'))
            else:
                login_attempts[input_user_id] = {'count': 0, 'first_attempt_time': current_time}

        # IDとパスワードの照合
        if input_user_id == USER_ID and input_password == PASSWORD:
            session['logged_in'] = True
            flash('ログインに成功しました！')
            login_attempts[input_user_id] = {'count': 0, 'first_attempt_time': current_time}
            return redirect(url_for('index'))
        else:
            login_attempts[input_user_id]['count'] += 1
            flash('IDまたはパスワードが間違っています')
            return redirect(url_for('login'))

    return render_template('login.html')

# ログアウト
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('ログアウトしました')
    return redirect(url_for('login'))

# ルートページ
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    people = Person.query.order_by(Person.order).all()
    return render_template('index.html', people=people)

# 全タスクの取得
@app.route('/all_tasks')
def all_tasks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    tasks = Task.query.order_by(Task.priority).all()
    return render_template('task_list.html', tasks=tasks, person_name=None)

# 担当者別タスクの取得
@app.route('/person_tasks/<int:person_id>')
def person_tasks(person_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    person = Person.query.get_or_404(person_id)
    tasks = Task.query.filter_by(person_id=person_id).order_by(Task.priority).all()
    return render_template('task_list.html', tasks=tasks, person_name=person.name)

# タスクの順序更新
@app.route('/update_task_order', methods=['POST'])
def update_task_order():
    if not session.get('logged_in'):
        return jsonify({'status': 'failed', 'message': 'Unauthorized'}), 401
    data = request.get_json()
    task_order = data.get('task_order', [])
    for index, task_id in enumerate(task_order):
        task = Task.query.get(task_id)
        if task:
            task.priority = index
    db.session.commit()
    return jsonify({'status': 'success'})

# 担当者の順序更新
@app.route('/update_person_order', methods=['POST'])
def update_person_order():
    if not session.get('logged_in'):
        return jsonify({'status': 'failed', 'message': 'Unauthorized'}), 401
    data = request.get_json()
    person_order = data.get('person_order', [])
    for index, person_id in enumerate(person_order):
        person = Person.query.get(person_id)
        if person:
            person.order = index
    db.session.commit()
    return jsonify({'status': 'success'})

# 担当者の追加・編集・削除
@app.route('/edit_person', methods=['GET', 'POST'])
def edit_person():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    people = Person.query.order_by(Person.order).all()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form['name']
            existing_person = Person.query.filter_by(name=name).first()
            if existing_person:
                flash('同じ名前の担当者がすでに存在します')
            else:
                max_order = db.session.query(db.func.max(Person.order)).scalar() or 0
                new_person = Person(name=name, order=max_order + 1)
                db.session.add(new_person)
                db.session.commit()
                flash('担当者が追加されました')
        elif action == 'edit':
            person_id = request.form['person_id']
            new_name = request.form['new_name']
            person = Person.query.get(person_id)
            if person:
                person.name = new_name
                db.session.commit()
                flash('担当者名が更新されました')
            else:
                flash('担当者が見つかりません')
        elif action == 'delete':
            person_id = request.form['person_id']
            person = Person.query.get(person_id)
            if person:
                db.session.delete(person)
                db.session.commit()
                flash('担当者が削除されました')
            else:
                flash('担当者が見つかりません')
        return redirect(url_for('edit_person'))
    return render_template('edit_person.html', people=people)

# タスクの追加
@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    people = Person.query.order_by(Person.order).all()
    if request.method == 'POST':
        content = request.form['content']
        person_id = request.form.get('person_id')
        deadline = request.form.get('deadline') or None
        min_priority = db.session.query(db.func.min(Task.priority)).scalar() or 0
        min_priority -= 1
        new_task = Task(content=content, person_id=person_id, priority=min_priority, deadline=deadline)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_task.html', people=people)

# タスクの編集
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    task = Task.query.get_or_404(id)
    people = Person.query.order_by(Person.order).all()
    if request.method == 'POST':
        task.content = request.form['content']
        task.deadline = request.form.get('deadline') or None
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_task.html', task=task, people=people)

# タスクの削除
@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('タスクが削除されました')
    return redirect(url_for('index'))

# robots.txtの設定（検索エンジンによるインデックスを防止）
@app.route('/robots.txt')
def robots_txt():
    return "User-agent: *\nDisallow: /", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=False)
