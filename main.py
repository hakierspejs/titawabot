#!/usr/bin/env python3

import logging
import atexit
import datetime
import socket
import time
import io
import signal

import telegram
import requests


CHAT_ID = -1001510902119
WZORCE = [
    "3565",
]


@atexit.register
def odczekaj_minute_przed_wyjsciem(*args, **kwargs):
    time.sleep(60.0)


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
            if buf == b"login:":
                s.send(login.encode() + b"\r\n")
                logging.info('zaloguj_sie: zalogowany?')
                return


def main():
    logging.info('Bot się uruchamia, za 10s nawiąże połączenie...')
    time.sleep(10.0)
    signal.alarm(60 * 60 * 3)
    s = socket.socket()
    s.connect(("ve7cc.net", 23))
    zaloguj_sie(s, "SP7KZK")
    bot = telegram.Bot(open("api_key.txt").read().strip())
    ostatnio_wyslano_propagacje = None
    while True:
        linia = wczytaj_linie(s)
        msg = linia.decode('utf8', 'ignore').strip()
        czas = datetime.datetime.now()
        if (
            czas.hour == 8
            and czas.minute == 0
            and czas.day != ostatnio_wyslano_propagacje
        ):
            logging.info('main(): publikuje propagacje...')
            ostatnio_wyslano_propagacje = czas.day
            content = requests.get(
                "http://www.hamqsl.com/solar101vhf.php",
                headers={"User-Agent": "curl/7.68.0"},
            ).content
            bot.send_message(chat_id=CHAT_ID, text="Dzień dobry, warunki na dziś:")
            bot.send_photo(chat_id=CHAT_ID, photo=io.BytesIO(content))
            time.sleep(5.0)
        znaleziono = False
        for wzorzec in WZORCE:
            if wzorzec in msg:
                znaleziono = True
        if msg and znaleziono:
            logging.info('main(): publikuje linie: %r', linia)
            bot.send_message(chat_id=CHAT_ID, text=msg)
            time.sleep(5.0)
        else:
            logging.info('main(): odrzucam linie: %r', linia)


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    main()
