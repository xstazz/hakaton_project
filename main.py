from flask import Flask, render_template
import plotly.graph_objs as go

app = Flask(__name__)


@app.route('/')
def index():
    # Данные для графика
    x_data = ['A', 'B', 'C', 'D']
    y_data = [3, 7, 2, 5]

    # Создание объекта для столбчатой диаграммы
    bar_chart = go.Bar(
        x=x_data,
        y=y_data
    )

    # Собираем график
    fig = go.Figure(data=[bar_chart])
    # Настройка макета
    fig.update_layout(title='Пример столбчатой диаграммы', xaxis_title='Категории', yaxis_title='Значения')

    # Конвертируем график в HTML строку
    graph_html = fig.to_html(full_html=False)

    # Передача HTML строки в шаблон и отображение
    return render_template('index.html', graph_html=graph_html)


if __name__ == '__main__':
    app.run(debug=True)
