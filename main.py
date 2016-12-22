from __future__ import absolute_import
import termios
import sys
import logging
import argparse
from intermode.client import Client
from intermode.exc import *
from intermode.container import *

LOG = logging.getLogger('intermode')

def main(argv):
    container = Container("127.0.0.1:2375", "4d97c277eaff", "v1.17")
    try:
        console = Client(container,
                         escape="~",
                         close_wait=0.5)

        console.start_loop()
    except ContainerWebSocketException as e:
        LOG.error(e)

if __name__ == '__main__':
    main(sys.argv)
