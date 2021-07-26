#!/usr/bin/env python3

import socket
import time
import sys

import telegram

s = socket.socket()
s.connect(("ve7cc.net", 23))


def wczytaj_linie(s):
    buf = b""
    while True:
        c = s.recv(1)
        buf += c
        if c == b"\n":
            return buf


buf = b""
while True:
    c = s.recv(1)
    buf += c
    if c == b"\n":
        buf = b""
    if c == b":":
        if buf == b"login:":
            s.send(b"SP7KZK\r\n")
            sys.stderr.write('Zalogowany...?\n')
            break


bot = telegram.Bot(open('api_key.txt').read().strip())
while True:
    linia = wczytaj_linie(s)
    msg = linia.decode().strip()
    print(msg)
    if msg and '3565' in msg:
        bot.send_message(chat_id=-548484028, text=msg)
        time.sleep(5.0)
