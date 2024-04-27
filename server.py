import json
import os
import sqlite3

import plotly
from flask import Flask, render_template, request, redirect, url_for, flash, session
from collections import defaultdict
import plotly.graph_objs as go

app = Flask(__name__)
app.secret_key = 'your_secret_key'

mash_list = [
    {"id": 1, "name": "Москва - Сочи", "price": 10},
    {"id": 2, "name": "Рязань - Тагил", "price": 8},
]
users_order = []
order = []

admin_username = 'admin'
admin_password = 'qwerty'

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
conn.commit()
conn.close()


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'username' in session:
        username = session['username']
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar.filename != '':
                avatar.save(os.path.join(app.root_path, 'static', 'avatars', username + '.jpg'))
                flash('Аватарка успешно загружена.', 'success')
            else:
                flash('Не выбран файл.', 'error')
        else:
            flash('Файл не найден.', 'error')
        return redirect(url_for('profile'))
    else:
        flash('Пожалуйста, войдите в систему, чтобы загрузить аватарку.', 'error')
        return redirect(url_for('index'))


@app.route('/login', methods=['POST', 'GET'])
def login_post():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and password == admin_password:
            session['username'] = username
            flash(f"Добро пожаловать, {username}!", 'success')
            return redirect(url_for('admin_panel'))
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and user[1] == password:
            session['username'] = username
            flash(f"Добро пожаловать, {username}!", 'success')
            return redirect(url_for('marsh'))
        flash("Неверное имя пользователя или пароль. Пожалуйста, попробуйте снова.", 'error')
    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Пароли не совпадают. Пожалуйста, попробуйте снова.", 'error')
        else:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, password))
            conn.commit()
            conn.close()
            flash(f"Регистрация успешна для пользователя: {username}", 'success')
            return redirect(url_for('marsh'))
    return render_template('register.html')


@app.route('/admin_panel')
def admin_panel():
    if 'username' in session and session['username'] == admin_username:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        orders = cursor.fetchall()
        vote_counts = defaultdict(int)
        for order in orders:
            vote_counts[order[2]] += 1

        # Создаем данные для голосов для построения графика
        labels = list(vote_counts.keys())
        values = list(vote_counts.values())

        # Создаем объект графика Plotly
        bar_chart = go.Bar(x=labels, y=values)

        # Создаем объект данных графика
        plot_data = [bar_chart]

        # Преобразуем объект данных графика в JSON для передачи в HTML
        plot_json = json.dumps(plot_data, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('admin_panel.html', data=orders, plot_json=plot_json)
    else:
        flash("Доступ к админ панели запрещен.", 'error')
        return redirect(url_for('index'))


@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    if 'username' in session and session['username'] == admin_username:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders")
        conn.commit()
        conn.close()
        flash("Заказы успешно очищены.", 'success')
        return redirect(url_for('admin_panel'))
    else:
        flash("Доступ запрещен.", 'error')
        return redirect(url_for('index'))


@app.route('/marsh')
def marsh():
    if 'username' in session:
        return render_template('marsh.html', mash_list=mash_list)
    else:
        flash("Пожалуйста, войдите в систему, чтобы получить доступ к меню.", 'error')
        return redirect(url_for('index'))


@app.route('/add_to_order/<int:mash_id>')
def add_to_order(mash_id):
    selected_mash = next((mash for mash in mash_list if mash["id"] == mash_id), None)
    if selected_mash:
        order.append(selected_mash)
    return redirect(url_for('marsh'))


@app.route('/view_order')
def view_order():
    total_price = sum(mash['price'] for mash in order)
    return render_template('order.html', order=order, total_price=total_price)


@app.route('/pay_order')
def pay_order():
    global users_order
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    for mash in order:
        cursor.execute('''
                INSERT INTO orders (mash_id, mash_name, mash_price)
                VALUES (?, ?, ?)
            ''', (mash['id'], mash['name'], mash['price']))
        users_order.append({'name': mash['name'], 'price': mash['price']})
    conn.commit()
    conn.close()
    order.clear()
    return redirect(url_for('marsh'))


@app.route('/clear_order')
def clear_order():
    global users_order
    for mash in order:
        users_order.append({'name': mash['name'], 'price': mash['price']})
    order.clear()
    return redirect(url_for('marsh'))


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user:
            username = user[0]
            email = user[1]
            return render_template('profile.html', username=username, email=email)
        else:
            flash("Не удалось загрузить данные профиля.", 'error')
            return redirect(url_for('index'))
    else:
        flash("Пожалуйста, войдите в систему, чтобы получить доступ к профилю.", 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mash_id INTEGER,
            mash_name TEXT,
            mash_price INTEGER
        )
    ''')
    conn.commit()
    conn.close()

    app.run(debug=True)
