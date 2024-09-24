from flask import Flask, render_template, request, redirect, url_for, flash, session
import configparser

app = Flask(__name__)

# config.ini の読み込み
config = configparser.ConfigParser()
config.read('config.ini')

# IDとパスワード、シークレットキーを設定ファイルから取得
USER_ID = config['DEFAULT'].get('USER_ID')  # デフォルトのUSER_IDを取得
PASSWORD = config['DEFAULT'].get('PASSWORD')  # パスワードも文字列として取得
app.secret_key = config['DEFAULT'].get('SECRET_KEY')

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_user_id = request.form['user_id']
        input_password = request.form['password']

        # IDとパスワードの照合
        if input_user_id == USER_ID and input_password == PASSWORD:
            session['logged_in'] = True
            flash('ログインに成功しました！')
            return redirect(url_for('index'))
        else:
            flash('IDまたはパスワードが間違っています')
            return redirect(url_for('login'))
    return render_template('login.html')

# ログアウト機能
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('ログアウトしました')
    return redirect(url_for('login'))

# ログイン済みユーザーにしかアクセスできないページ
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

# メインのアプリがここに追加される（今回は省略）

if __name__ == '__main__':
    app.run(debug=False)
