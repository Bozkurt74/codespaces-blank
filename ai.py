import tkinter as tk
import speech_recognition as sr
import pyttsx3
import datetime
import requests
import threading
import geopy
from geopy.geocoders import Nominatim
import spacy
import matplotlib.pyplot as plt
from apscheduler.schedulers.background import BackgroundScheduler
import cv2
import face_recognition
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# API anahtarları
WEATHER_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'  # Hava durumu API anahtarı
NEWS_API_KEY = 'YOUR_NEWSAPI_KEY'  # Haber API anahtarı
GOOGLE_CREDENTIALS_FILE = 'path_to_your_credentials.json'  # Google API kimlik bilgileri

# Sesli yanıt motorunu başlat
engine = pyttsx3.init()
nlp = spacy.load("tr_core_news_sm")  # Türkçe NLP modeli

# Kullanıcı profili
user_profile = {
    "name": "Kullanıcı",
    "reminders": []
}

# Sesli yanıt fonksiyonu
def speak(text):
    """Verilen metni sesli olarak okur."""
    engine.say(text)
    engine.runAndWait()

# Ses kaydetme ve dinleme
def listen():
    """Kullanıcıdan sesli komut alır ve metne çevirir."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Dinliyorum...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio, language='tr-TR')
            print(f"Kullanıcı Komutu: {command}")
            return command
        except sr.UnknownValueError:
            print("Anlaşılamadı.")
            return ""
        except sr.RequestError:
            print("Bağlantı hatası.")
            return ""

# Hava durumu alma
def get_weather(city):
    """Verilen şehir için hava durumunu alır."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&lang=tr&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        weather_description = data['weather'][0]['description']
        return f"{city} için hava durumu: {temp} derece, {weather_description}."
    else:
        return "Hava durumu bilgisi alınamadı."

# Lokasyona göre hava durumu alma
def get_location_weather():
    """Kullanıcının konumuna göre hava durumu alır."""
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode("Türkiye")  # Örnek olarak Türkiye'nin hava durumu
    return get_weather(location.address)

# Hava durumu grafik gösterimi
def plot_weather_data(city):
    """Verilen şehir için hava durumu verilerini grafik olarak gösterir."""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&lang=tr&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        times = [item['dt_txt'] for item in data['list']]
        temps = [item['main']['temp'] for item in data['list']]
        
        plt.figure(figsize=(10, 5))
        plt.plot(times, temps, marker='o')
        plt.title(f"{city} Hava Durumu Tahminleri")
        plt.xlabel('Zaman')
        plt.ylabel('Sıcaklık (°C)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        speak("Hava durumu grafik bilgisi alınamadı.")

# Yüz tanıma
def face_recognition_system():
    """Yüz tanıma sistemini başlatır."""
    video_capture = cv2.VideoCapture(0)
    known_face_encodings = []  # Tanınmış yüz kodlamaları
    known_face_names = []      # Tanınmış yüz isimleri

    while True:
        ret, frame = video_capture.read()
        rgb_frame = frame[:, :, ::-1]

        # Yüzleri bul
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Bilinmeyen"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            # Yüzün etrafında bir dikdörtgen çiz
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Sonuçları göster
        cv2.imshow('Yüz Tanıma', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

# Google Takvim'e etkinlik ekleme
def add_event_to_calendar(event):
    """Google Takvim'e verilen etkinliği ekler."""
    creds = Credentials.from_authorized_user_file(GOOGLE_CREDENTIALS_FILE, ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    # Etkinlik bilgileri
    event_body = {
        'summary': event,
        'start': {
            'dateTime': datetime.datetime.now().isoformat(),
            'timeZone': 'Europe/Istanbul',
        },
        'end': {
            'dateTime': (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': 'Europe/Istanbul',
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event_body).execute()
    speak(f"Takvime {event} etkinliği eklendi.")

# Komut analiz etme
def analyze_command(command):
    """Kullanıcı komutunu analiz eder ve kelime etiketlerini yazdırır."""
    doc = nlp(command)
    for token in doc:
        print(token.text, token.pos_)  # Kelimeleri ve etiketlerini yazdır

# Komutları işleme
def process_command(command):
    """Kullanıcının verdiği komutu işler ve uygun yanıtı verir."""
    command = command.lower()
    analyze_command(command)  # Komutu analiz et

    if 'merhaba' in command:
        speak(f"Merhaba {user_profile['name']}! Size nasıl yardımcı olabilirim?")
    elif 'saat' in command:
        current_time = datetime.datetime.now().strftime("%H:%M")
        speak(f"Şu an saat {current_time}.")
    elif 'tarih' in command:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        speak(f"Bugün {current_date}.")
    elif 'nasılsın' in command:
        speak("Ben bir yapay zeka modeliyim, ama teşekkür ederim! Siz nasılsınız?")
    elif 'hava durumu' in command:
        speak("Hangi şehir için hava durumu öğrenmek istersiniz?")
        city = listen()
        if city:
            weather_report = get_weather(city)
            speak(weather_report)
            plot_weather_data(city)  # Hava durumu grafik gösterimi
        else:
            speak("Şu an konumunuz için hava durumu bilgisi alıyorum.")
            weather_report = get_location_weather()
            speak(weather_report)
    elif 'hatırlat' in command:
        speak("Hatırlatıcı için neyi ayarlamak istersiniz?")
        reminder = listen()
        if reminder:
            schedule_reminder(reminder)
    elif 'takvim' in command:
        speak("Takvim için ne eklemek istersiniz?")
        event = listen()
        add_event_to_calendar(event)  # Google Takvim'e etkinlik ekleme
    elif 'çık' in command:
        speak("Görüşürüz!")
        return False
    else:
        speak("Bu komutu anlamadım. Lütfen tekrar deneyin.")

    return True

# Hatırlatıcıları ayarlama
def schedule_reminder(reminder):
    """Kullanıcı için hatırlatıcı ayarlar."""
    scheduler = BackgroundScheduler()
    reminder_time = datetime.datetime.now() + datetime.timedelta(seconds=10)  # 10 saniye sonra hatırlat
    scheduler.add_job(lambda: speak(f"Hatırlatıcı: {reminder}"), 'date', run_date=reminder_time)
    scheduler.start()
    speak("Hatırlatıcı ayarlandı.")

# Asistanı çalıştırma
def run_assistant():
    """Asistanı başlatır ve sürekli dinlemeye devam eder."""
    speak("Akıllı asistan çalışmaya başladı.")
    while True:
        command = listen()
        if not command:
            continue
        if not process_command(command):
            break

# GUI Arayüzü
def start_assistant():
    """Asistanı başlatma işlevi."""
    threading.Thread(target=run_assistant).start()

# Ana pencereyi oluştur
window = tk.Tk()
window.title("Akıllı Asistan")
window.geometry("400x300")

# Başlatma butonu
button = tk.Button(window, text="Asistanı Başlat", command=start_assistant)
button.pack(pady=20)

# Yüz tanıma butonu
face_button = tk.Button(window, text="Yüz Tanıma Başlat", command=face_recognition_system)
face_button.pack(pady=20)

# Ana döngüyü başlat
window.mainloop()
