#!/usr/bin/env python3

import logging
import atexit
import datetime
import socket
import time
import io
import signal
import ast
import telegram
import requests
import os


CHAT_ID = -1001510902119
CHAT_ID_2 = -1001781769718
WZORCE = [
    "3565",
]
prefixy = ["SP","SN","SO","SQ","3Z"]
wyjatki = ["F4VSQ","HB9EGA"]
znaki_do_sprawdzenia = {}
znaki_statystyka = {}
plik_z_statystykami ="/tmp/slownik/slownik.txt"
staty = ""

@atexit.register
def odczekaj_minute_przed_wyjsciem():
    time.sleep(60.0)

def sprawdz_czy_plik_statystyk_istnieje(plik_do_sprawdzenia):
    if os.path.isfile(plik_do_sprawdzenia):
        logging.info('Plik istnieje')
        pass
    else:
        logging.info('Plik nie istnieje, tworze !')
        plik = open(plik_do_sprawdzenia, "w")
        plik.write("{}")
        plik.close()

def zapisz_statystyke_do_pliku(slownik,plik):
    with open(plik,"w") as file:
      file.write(str(slownik))

def odczytaj_statystyke_z_pliku(plik):
    #slownik = {}
    #zawartosc = ""
    file = open(plik, "r")
    zawartosc = file.read()
    slownik = ast.literal_eval(zawartosc)
    file.close()
    return slownik

def wczytaj_linie(s):
    buf = b""
    while True:
        c = s.recv(1)
        buf += c
        if c == b"\n":
            return buf

def zaloguj_sie(s, login):
    buf = b""
    while True:
        c = s.recv(1)
        buf += c
        if c == b"\n":
            logging.debug('zaloguj_sie: odrzucam linię: %r', buf)
            buf = b""
        if c == b":":
            if buf == b"Please enter your call:":
                s.send(login.encode() + b"\r\n")
                logging.info('zaloguj_sie: zalogowany?')
                return

def main():
    logging.info('Bot się uruchamia, za 10s nawiąże połączenie...')
    time.sleep(10.0)
    signal.alarm(60 * 60)
    s = socket.socket()
    s.settimeout(60)
    s.connect(("telnet.reversebeacon.net", 7000))
    zaloguj_sie(s, "SP7KZK")
    bot = telegram.Bot(open("api_key.txt").read().strip())
    bot.send_message(chat_id=CHAT_ID, text="Bot się uruchamia")
    bot.send_message(chat_id=CHAT_ID_2, text="Bot się uruchamia")
    ostatnio_wyslano_propagacje = None
    ostatnio_wyslano_statystyke = None
    time.sleep(30)
    logging.info('Sprawdzam czy plik logow istnieje')
    sprawdz_czy_plik_statystyk_istnieje(plik_z_statystykami)
    logging.info('Wczytuje slownik z pliku')
    znaki_statystyka = odczytaj_statystyke_z_pliku(plik_z_statystykami)
    logging.info('Slownik :')
    logging.info(znaki_statystyka)
    czas = datetime.datetime.utcnow()
    ostatnio_wyslano_statystyke = czas.month
    while True:
        linia = wczytaj_linie(s)
        msg = linia.decode('utf8', 'ignore').strip()
        msg_split = msg.split()
        try:
            znak = msg_split[4]
        except IndexError:
            znak = ""
        czas = datetime.datetime.utcnow()
        if czas.month != ostatnio_wyslano_statystyke:
            znaki_statystyka.clear()
            zapisz_statystyke_do_pliku(znaki_statystyka,plik_z_statystykami)
            ostatnio_wyslano_statystyke = czas.month
        if (
            czas.hour == 6
            and czas.minute == 0
            and czas.day != ostatnio_wyslano_propagacje
        ):
            logging.info('main(): publikuje propagacje i statystyki...')
            ostatnio_wyslano_propagacje = czas.day
            content = requests.get(
                "http://www.hamqsl.com/solar101vhf.php",
                headers={"User-Agent": "curl/7.68.0"},
            ).content
            bot.send_message(chat_id=CHAT_ID, text="Dzień dobry, warunki na dziś:")
            bot.send_photo(chat_id=CHAT_ID, photo=io.BytesIO(content))

            posortowane = sorted(znaki_statystyka.items(),key=lambda x:x[1],reverse=True)
            slownik_posortowany = {}
            for i in posortowane:
                #print(i[0], i[1])
                slownik_posortowany[i[0]] = i[1]
            slownik_posortowany_usun_szum = {}
            for i in slownik_posortowany:
                if slownik_posortowany[i] > 30:
                    slownik_posortowany_usun_szum[i] = slownik_posortowany[i]
            staty = ""
            for x in slownik_posortowany_usun_szum:
                part = x[:2]
                sp = False
                exception = False
                for i in prefixy:
                    if part == i:
                        sp = True
                for i in wyjatki:
                    if i == x:
                        exception = True
                if sp or exception:
                    statystyka = str(x) + " : " + str(slownik_posortowany_usun_szum[x]) + " razy" + "\n"
                    staty = staty + statystyka
            time.sleep(5)
            if staty:
                bot.send_message(chat_id=CHAT_ID, text="Stacje SP słyszane stacje w tym miesiącu:")
                bot.send_message(chat_id=CHAT_ID, text=staty)
                time.sleep(5.0)
        znaleziono = False
        znaleziono_znak = False
        for wzorzec in WZORCE:
            if wzorzec in msg:
                znaleziono = True

        if znaleziono:
            if znak in znaki_statystyka:
                znaki_statystyka[znak] = znaki_statystyka[znak] +1
                zapisz_statystyke_do_pliku(znaki_statystyka,plik_z_statystykami)
                logging.info('main(): Plus 1 do statystuki dla : %r', znak)
            else:
                znaki_statystyka[znak] = 1
                zapisz_statystyke_do_pliku(znaki_statystyka,plik_z_statystykami)
                logging.info('main(): Pierwszy hit dla : %r', znak)

            if znak in znaki_do_sprawdzenia:
                logging.info('main(): znalazlem znak w slowniku %r', znak)
                czas_kiedy_slyszalem_znak = znaki_do_sprawdzenia[znak]
                czas_aktualny = time.time()
                jak_dawno_slyszalem = czas_aktualny - czas_kiedy_slyszalem_znak
                logging.info('main(): Znak słyszałem ile temu : %r', jak_dawno_slyszalem)
                if jak_dawno_slyszalem > 1800:
                    logging.info('main(): Znak slyszalem dawniej niz 30 minut')
                    znaki_do_sprawdzenia[znak] = time.time()
                    znaleziono_znak = True
                else:
                    logging.info('main(): Znak slyszalem mniej niz 30 minut temu - POMIJAM!')
            else:
                znaleziono_znak = True
                znaki_do_sprawdzenia[znak] = time.time()
                logging.info('main(): Brak znaku w słowniku - DODAJE!')

        if msg and znaleziono and znaleziono_znak:
            logging.info('main(): publikuje linie: %r', linia)
            bot.send_message(chat_id=CHAT_ID_2, text=msg)
            time.sleep(5.0)
        #else:
        #    logging.info('main(): odrzucam linie: %r', linia)


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    main()
