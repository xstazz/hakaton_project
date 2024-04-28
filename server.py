import json
import os
import sqlite3

import plotly
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from collections import defaultdict
import plotly.graph_objs as go
from regions import DATA_REGIONS, DATA_REGIONS2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

true_value_received = False

mash_list = DATA_REGIONS

users_order = {}
order = []

admin_username = 'admin'
admin_password = 'qwerty'
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  voices INTEGER DEFAULT 0,
                  price INTEGER DEFAULT 0
                  )''')

conn.commit()
conn.close()


@app.route('/')
def index():
    return render_template('main.html')


@app.route('/geo_admin')
def geo_admin():
    return render_template('geo_admin.html')


@app.route('/save_coords_as_text', methods=['GET'])
def save_coords_as_text():
    coords = request.args.get('coords')

    # Открываем файл для записи и записываем координаты
    with open('static/coords.txt', 'a') as file:
        file.write(coords + '\n')

    return 'Coordinates saved successfully!'


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/return_true', methods=['POST'])
def return_true():
    global true_value_received
    true_value_received = True
    print(true_value_received)
    return redirect(url_for('admin_panel'))


@app.route('/Rus_diam')
def Rus_diam():
    if true_value_received:
        conn = sqlite3.connect('orders2.db')
    else:
        conn = sqlite3.connect('orders.db')

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    vote_counts = defaultdict(int)
    for order in orders:
        vote_counts[order[2]] += 1

    # Create data for votes to build the chart
    labels = list(vote_counts.keys())
    values = list(vote_counts.values())

    # Create a Plotly chart object
    bar_chart = go.Bar(x=labels, y=values)

    # Create chart data object
    plot_data = [bar_chart]

    # Convert the chart data object to JSON for passing to HTML
    plot_json = json.dumps(plot_data, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('Rus_diam.html', data=orders, plot_json=plot_json)


@app.route('/routes')
def routes():
    return render_template('routes.html')


@app.route('/get_coordinates')
def get_coordinates():
    try:
        with open('static/coords.txt', 'r') as file:
            coordinates = eval(file.read())  # Используем eval для преобразования текста из файла в список координат
        return jsonify(coordinates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/vote')
def vote():
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

    return render_template('vote.html', data=orders, plot_json=plot_json)


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
        labels = list(vote_counts.keys())
        values = list(vote_counts.values())
        bar_chart = go.Bar(x=labels, y=values)
        plot_data = [bar_chart]
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
        if true_value_received:
            mash_list = DATA_REGIONS2
        else:
            mash_list = DATA_REGIONS
        return render_template('marsh.html', mash_list=mash_list)
    else:
        flash("Please log in to access the menu.", 'error')
        return redirect(url_for('index'))


@app.route('/add_to_order/<int:mash_id>')
def add_to_order(mash_id):
    selected_mash = next((mash for mash in mash_list if mash["id"] == mash_id), None)
    if selected_mash:
        order.append(selected_mash)
    return redirect(url_for('marsh'))


@app.route('/view_order')
def view_order():
    total_price = sum(mash['voice'] for mash in order)

    if 'username' in session:
        username = session['username']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT voices FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            current_balance = user[0]
            new_balance = current_balance - total_price

            if new_balance >= 0:
                # Update the database with the new balance
                cursor.execute("UPDATE users SET voices = ? WHERE username = ?", (new_balance, username))
                conn.commit()
            else:
                flash("Недостаточно средств для оплаты заказа.", 'error')
                conn.close()
                return redirect(url_for('marsh'))

            conn.close()
            return render_template('order.html', order=order, total_price=total_price, new_balance=new_balance)
        else:
            flash("Не удалось загрузить данные профиля.", 'error')
            conn.close()
            return redirect(url_for('index'))
    else:
        flash("Пожалуйста, войдите в систему, чтобы получить доступ к профилю.", 'error')
        return redirect(url_for('index'))


@app.route('/pay_order')
def pay_order():
    global users_order
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    for mash in order:
        cursor.execute('''
                INSERT INTO orders (mash_id, mash_name, mash_voice)
                VALUES (?, ?, ?)
            ''', (mash['id'], mash['name'], mash['voice']))
        users_order[mash['id']] = {'name': mash['name'], 'voice': mash['voice']}
    conn.commit()
    conn.close()
    order.clear()
    return redirect(url_for('marsh'))


@app.route('/clear_order')
def clear_order():
    global users_order
    for mash in order:
        users_order[mash['id']] = {'name': mash['name'], 'voice': mash['voice']}
    order.clear()
    return redirect(url_for('marsh'))


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, voices, price FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        print(user)
        if user:
            username = user[0]
            email = user[1]
            balance = user[2]
            price = user[3]
            return render_template('profile.html', username=username, email=email, balance=balance, price=price)
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
            mash_voice INTEGER
        )
    ''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect('orders2.db')
    cursor = conn.cursor()
    cursor.execute('''
           CREATE TABLE IF NOT EXISTS orders (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               mash_id INTEGER,
               mash_name TEXT,
               mash_voice INTEGER
           )
       ''')
    conn.commit()
    conn.close()

    app.run(debug=True)
