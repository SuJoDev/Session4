from flask import Flask, render_template, request
import calendar
from datetime import datetime

app = Flask(__name__)

# Пример данных с событиями
events = [
    {
        "id": 1,
        "name": "Совещание админимтрации",
        "discription": "Коллеги, я все понимаю, но туалет не просто так придумали. Нужно выяснить у кого недержание",
        "ev_date": "2025-02-25",
        "author_name": "Воронова Устинья Митрофановна"
    },
    {
        "id": 2,
        "name": "Буткемп",
        "discription": "Пацаны, пока начальник в отпуске го катку в дотку",
        "ev_date": "2025-02-05",
        "author_name": "Суханов Эрнест Петрович"
    },
    {
        "id": 3,
        "name": "Пикник",
        "discription": "Ухожу в отпуск летом, кто со мной на шашлычек?",
        "author_name": "Яковлева Аделия Геласьевна",
        "ev_date": "2025-02-05"
    }
]

@app.route('/', methods=['GET', 'POST'])
def index():
    # Получаем текущий год и месяц, если они не переданы в запросе, используем текущие
    year = 2025  # default year
    month = 2  # default month

    # Обрабатываем POST запрос
    if request.method == 'POST':
        # Если переданы значения для месяца и года в форме
        if 'year' in request.form and 'month' in request.form:
            year = int(request.form['year'])
            month = int(request.form['month'])
        
        # Логика переключения месяцев
        if 'prev' in request.form:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        elif 'next' in request.form:
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1

    # Генерация календаря
    cal = calendar.monthcalendar(year, month)

    # Получаем название месяца
    month_name = calendar.month_name[month]

    # Преобразуем события в словарь с датами для быстрого поиска
    event_dict = {}
    for event in events:
        event_date = datetime.strptime(event['ev_date'], '%Y-%m-%d').date()
        if event_date.month == month and event_date.year == year:
            if event_date not in event_dict:
                event_dict[event_date] = []
            event_dict[event_date].append(event)

    # Передаем данные в шаблон
    return render_template('index2.html', calendar=cal, year=year, month=month, month_name=month_name, event_dict=event_dict)

if __name__ == '__main__':
    app.run(debug=True)
