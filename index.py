from flask import Flask, render_template, request, send_file

import qrcode
import io

import requests
import xml.etree.ElementTree as Et

import locale

import threading
import time

import calendar

from datetime import datetime

app = Flask(__name__)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


lastest_news = []
stuff_members = []
events = []

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

def generate_qr(vcard):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=2)
    qr.add_data(vcard)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    return img

def get_free_day():
    response = requests.get("http://127.0.0.1:8000/calendar_work")
    if response.status_code == 200:
        exceptions = response.json()
        return exceptions
    return []

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
        
def get_free_day():
    response = requests.get("http://127.0.0.1:8000/calendar_work")
    if response.status_code == 200:
        return response.json()
    else:
        return []
        
@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.args.get('search', '').lower()

    get_events()
    get_stuff()
    exceptions = get_free_day()
    
    year = 2025
    month = 3

    if request.method == 'POST':
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
                month +=1 
    
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

    now = datetime.now()
    
    filtered_stuff = [item for item in stuff_members if search_query in item['name'].lower() or search_query in item['post'].lower()]
    filtered_events = [item for item in events if search_query in item['name'].lower() or search_query in item['discription'].lower()]

    non_working_days = {item['exception_date'] for item in exceptions if not item['is_working_day']}

    return render_template('index.html', stuff=filtered_stuff, events=filtered_events, calendar=cal, year=year,
                           month=month, month_name=month_name, event_dict=event_dict, event_count=event_count, now=now, non_working_days=non_working_days, datetime=datetime)
    
if __name__ == "__main__":
    app.run(debug=True)
