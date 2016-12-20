from __future__ import absolute_import
import tty
import termios
import sys
import logging
import argparse
from intermode.client import Client
from intermode.exc import *

LOG = logging.getLogger('intermode')

def main(argv):
    console_url = "ws://10.169.42.35:2375/v1.17/containers/02fc882b5df8/attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"
    try:
        console = Client(console_url,
                         escape="~",
                         close_wait=0.5)

        console.start_loop()
    except ContainerWebSocketException as e:
        LOG.error(e)

if __name__ == '__main__':
    main(sys.argv)
