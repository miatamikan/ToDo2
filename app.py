from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セキュリティ上、環境変数から読み込むことを推奨します
csrf = CSRFProtect(app)

# パスワード設定（ここでパスワードを変更できます）
PASSWORD = '1111'

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

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('パスワードが間違っています')
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

# 以下、他のルート関数はセッションチェックを追加します

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
        min_priority = db.session.query(db.func.min(Task.priority)).scalar()
        if min_priority is None:
            min_priority = 0
        else:
            min_priority -= 1
        new_task = Task(content=content, person_id=person_id, priority=min_priority)
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
        task.person_id = request.form.get('person_id')
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

# robots.txtの設定
@app.route('/robots.txt')
def robots_txt():
    return "User-agent: *\nDisallow: /", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=False)
