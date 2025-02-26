from flask import Flask, render_template, request, send_file
import qrcode
import io
import requests
import xml.etree.ElementTree as ET
import threading
import time

import locale

import calendar 
from datetime import datetime

app = Flask(__name__)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

# Глобальная переменная для хранения последних новостей
latest_news = []
stuff_members = []
events = []

# Генерация vCard для QR-кода
def generate_vcard(name, email, phone, position):
    vcard = f"""BEGIN:VCARD
        VERSION:3.0
        N:{name.split()[-1]} 
        FN:{name}
        ORG:Ваша компания
        TITLE:{position}
        TEL;WORK;VOICE:{phone}
        EMAIL;WORK;INTERNET:{email}
        END:VCARD"""
    return vcard

# Генерация QR-кода
def generate_qr(vcard):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=2)
    qr.add_data(vcard)
    qr.make(fit=True)

    # Генерация изображения QR-кода
    img = qr.make_image(fill='black', back_color='white')

    return img

def get_events():
    global events
    response = requests.get("http://127.0.0.1:8000/ev/get")
    if response.status_code == 200:
        events = response.json()

def get_stuff():
    global stuff_members
    response = requests.get("http://127.0.0.1:8000/stuff_nofk")
    if response.status_code == 200:
        stuff_members = response.json()

def fetch_news():
    global latest_news
    while True:
        try:
            response = requests.get("https://192.168.1.85:5000/swagger")  # Замените на реальный URL RSS
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                news_items = []
                for item in root.findall(".//item"):
                    title = item.find("title").text
                    summary = item.find("description").text
                    link = item.find("link").text
                    news_items.append({"title": title, "summary": summary, "link": link})
                latest_news = news_items[:4]
        except Exception as e:
            print(f"Ошибка при загрузке RSS: {e}")
        time.sleep(15)

# Запуск фонового потока для обновления новостей
threading.Thread(target=fetch_news, daemon=True).start()

def get_free_day():
    response = requests.get("http://127.0.0.1:8000/calendar_work")
    if response.status_code == 200:
        exceptions = response.json()
        return exceptions
    return []


@app.route('/generate_qr', methods=['GET'])
def generate_qr_image():
    name = request.args.get('name')
    email = request.args.get('email')
    phone = request.args.get('phone')
    position = request.args.get('position')

    vcard = generate_vcard(name, email, phone, position)
    qr_image = generate_qr(vcard)

    img_io = io.BytesIO()
    qr_image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.args.get('search', '').lower()
    
    get_stuff()
    get_events()
    exceptions = get_free_day()
    
    year = 2025
    month = 2
    
    if request.method == 'POST':
        if 'year' in request.form and 'month' in request.form:
            year = int(request.form['year'])
            month = int(request.form['month'])
            
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
                
    cal = calendar.monthcalendar(year, month)
    
    months_russian = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь"
    }
    month_name = months_russian[month]
    
    event_dict = {}
    for event in events:
        event_date = datetime.strptime(event['ev_date'], '%Y-%m-%d').date()
        if event_date.month == month and event_date.year == year:
            if event_date not in event_dict:
                event_dict[event_date] = []
            event_dict[event_date].append(event)
    
    # Подсчет количества событий
    event_count = {date: len(event_list) for date, event_list in event_dict.items()}
    
    filtered_stuff = [item for item in stuff_members if search_query in item['name'].lower() or search_query in item['post'].lower()]
    filtered_events = [item for item in events if search_query in item['name'].lower() or search_query in item['discription'].lower()]
    filtered_news = [item for item in latest_news if search_query in item['title'].lower() or search_query in item['summary'].lower()]
    
    now = datetime.now()
    
    non_working_days = {item['exception_date'] for item in exceptions if not item['is_working_day']}

    return render_template('index.html', news=filtered_news, stuff=filtered_stuff, events=filtered_events, calendar=cal, year=year,
                           month=month, month_name=month_name, event_dict=event_dict, event_count=event_count, now=now, non_working_days=non_working_days, datetime=datetime)

@app.route('/download_event', methods=['GET'])
def download_event():
    summary = request.args.get('summary')
    start = request.args.get('start')
    description = request.args.get('discription', '')
    location = request.args.get('location', '')
    organizer = request.args.get('organizer', '')

    # Форматирование даты
    dt_start = start.replace("-", "") + "T000000Z"  # Убедитесь, что формат даты правильный
    dt_stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

    ics_content = f"""BEGIN:VCALENDAR
                VERSION:2.0
                BEGIN:VEVENT
                SUMMARY:{summary}
                DTSTART:{dt_start}
                DTEND:{dt_start}
                DTSTAMP:{dt_stamp}
                UID:{int(time.time())}
                DESCRIPTION:{description}
                LOCATION:{location}
                ORGANIZER:{organizer}
                STATUS:CONFIRMED
                PRIORITY:0
                END:VEVENT
                END:VCALENDAR
                """

    # Отправка файла для скачивания
    return send_file(io.BytesIO(ics_content.encode()), mimetype='text/calendar', as_attachment=True, download_name='event.ics')

if __name__ == '__main__':
    app.run(debug=True)
