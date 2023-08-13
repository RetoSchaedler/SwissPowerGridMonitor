import requests
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText


def getSwissgridNetzabweichung():
    # Basis-URL
    base_url = 'https://www.swissgrid.ch'

    # URL der Hauptseite
    main_page_url = base_url + '/de/home/operation/regulation/frequency.html'

    # Daten-URL
    data_url = base_url + '/bin/services/apicache?path=/content/swissgrid/de/home/operation/regulation/frequency/jcr:content/parsys/chart_copy'

    # Session erstellen
    session = requests.Session()

    # Hauptseite abrufen, um Cookies zu speichern
    response = session.get(main_page_url)
    response.raise_for_status() 

    # Jetzt, wo die Cookies in der Session gespeichert sind, die Daten-URL abrufen
    data_response = session.get(data_url)
    data_response.raise_for_status()

    data = data_response.json()  # Annahme, dass die Antwort JSON-Daten enthält

    # Extrahieren der Netzabweichung
    for entry in data['table']:
        if entry['label'] == 'Aktuelle Netzzeitabweichung':
            value = entry['value']
            break
    valueAbweichung=float(value[:-2]) # umwandlung von Text in Float


    # Extrahieren der Netzfrequenz
    for entry in data['table']:
        if entry['label'] == 'Aktuelle Frequenz':
            value = entry['value']
            break
    valueFrequenz=float(value[:-3]) # umwandlung von Text in Float


    return(valueAbweichung,valueFrequenz)


def send_email(subject, message, to_email):
    # Ihre E-Mail-Details
    SMTP_SERVER = "YOUR EMAIL SERVER"  # Der SMTP-Server Ihres E-Mail-Anbieters
    SMTP_PORT = 465  # Standardport für SMTP über SSL
    SMTP_USERNAME = "ENTER HERE YOUR SMTP USERNAME"  # Ihre E-Mail-Adresse
    SMTP_PASSWORD = "ENTER HERE YOUR SMTP PASSWORD"  # Ihr E-Mail-Passwort
    
    # Erstellung der E-Mail
    msg = MIMEText(message)
    msg["Power"] = subject
    msg["From"] = SMTP_USERNAME
    msg["Bcc"] = ', '.join(to_email)

    # Verbindung zum SMTP-Server herstellen und E-Mail senden
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())    

interval=300 # Abfrage alle 5min
maxAbweichungZeit=300 # Max. 5min Netz-Zeit-Abweichung absolut
maxAbweichungFreq=0.5 # 50Hz +/-0.5

# Variable, um den Zeitpunkt des letzten E-Mail-Versands zu speichern
last_email_sent = None

to_addresses = ['email1@yourproviderabc.com', 'email2@yourproviderabc.com']

while True:
    try:
        abweichung,frequenz=getSwissgridNetzabweichung()
        jetzt = datetime.now()
        zeitstempel = jetzt.strftime('%d.%m.%Y %H:%M:%S')
        print(zeitstempel+' Zeitabweichung: '+str(abweichung)+' Sec. Frequenz: '+str(frequenz)+' Hz')
        message=''
        if (abs(abweichung)>maxAbweichungZeit):
            print('Netz-Zeitabweichung zu gross')
            message=zeitstempel+'\nNetz-Zeit-Abweichung zu gross: '+str(abweichung)+' Sekunden absolut\nFrequenz: '+str(frequenz)+' Hz\n'
        if (abs(50-frequenz)>maxAbweichungFreq):
            print('Frequenzabweichung zu gross')
            message=zeitstempel+'\nNetz-Frequenz-Abweichung zu gross: '+str(frequenz)+' Hz\n'
    except:
        print('ERROR')
        
    if message!='' and (last_email_sent is None or (datetime.now() - last_email_sent) > timedelta(days=1)):
        send_email("Power Grid Alert", message, to_addresses)
        last_email_sent = datetime.now()
    time.sleep(interval)
