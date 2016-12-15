from __future__ import absolute_import
import tty
import termios
import sys
import logging
from intermode.client import Client
from intermode.exc import *

LOG = logging.getLogger('novaconsole')

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def getpass(maskchar = "*"):
    password = ""
    while True:
        ch = getch()
        if ch == "\r" or ch == "\n":
            print
            return password
        elif ch == "\b" or ord(ch) == 127:
            if len(password) > 0:
                sys.stdout.write("\b \b")
                password = password[:-1]
        else:
            if maskchar != None:
                sys.stdout.write(maskchar)
            password += ch

def main():
    console_url = "ws://127.0.0.1:2375/v1.17/containers/88d18194bc31/attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"
    #console_url = "ws://10.369.36.100:2375/v1.17/containers/5b4278fd22f9/attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"
    LOG.debug("Begin")
    try:
        console = Client(console_url,
                         escape="~",
                         close_wait=0.5)

        console.start_loop()
    except ContainerWebSocketException as e:
        LOG.error(e)

if __name__ == '__main__':
    main()
