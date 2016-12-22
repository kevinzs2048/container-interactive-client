from __future__ import absolute_import

import logging
import os
import select
import socket
import sys
import time
import six
import signal
import fcntl
import tty
import struct
import errno

import pycurl

import termios
from intermode.exc import *
from intermode.container import *

try:
    import websocket
except ImportError:
    logging.fatal('This package requires the "websocket" module.')
    logging.fatal('See http://pypi.python.org/pypi/websocket-client for '
                  'more information.')
    sys.exit()


class Client (object):
    def __init__(self, container,
                 escape='~',
                 close_wait=0.5):
        self.escape = escape
        self.close_wait = close_wait
        self.container = container
        #logging.getLogger().setLevel(logging.DEBUG)
        self.connect()

    #def setup_logging(self):
        #self.log = logging.getLogger('intermode')

    def connect(self):
        ip = self.container.host_ip
        id = self.container.container_id
        version = self.container.remote_api_ver

        url = "ws://" + ip + "/" + version + "/containers/" +\
              id + "/attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"

        logging.debug('connecting to: %s', url)
        try:
            self.ws = websocket.create_connection(url)
            logging.warn('connected to: %s', url)
            logging.warn('type "%s." to disconnect',
                          self.escape)
        except socket.error as e:
            raise ConnectionFailed(e)
        except websocket.WebSocketConnectionClosedException as e:
            raise ConnectionFailed(e)

    def start_loop(self):
        self.poll = select.poll()
        self.poll.register(sys.stdin,
                           select.POLLIN|select.POLLHUP|select.POLLPRI)
        self.poll.register(self.ws,
                           select.POLLIN|select.POLLHUP|select.POLLPRI)

        self.start_of_line = False
        self.read_escape = False
        with WINCHHandler(self):
            try:
                self.setup_tty()
                self.run_forever()
            except socket.error as e:
                raise ConnectionFailed(e)
            except websocket.WebSocketConnectionClosedException as e:
                raise Disconnected(e)
            finally:
                self.restore_tty()

    def run_forever(self):
        logging.debug('starting main loop in client')
        self.quit = False
        quitting = False
        when = None

        while True:
            try:
                for fd, event in self.poll.poll(500):
                    if fd == self.ws.fileno():
                        self.handle_websocket(event)
                    elif fd == sys.stdin.fileno():
                        self.handle_stdin(event)
            except select.error as e:
                # POSIX signals interrupt select()
                no = e.errno if six.PY3 else e[0]
                if no == errno.EINTR:
                    continue
                else:
                    raise e

            if self.quit and not quitting:
                self.log.debug('entering close_wait')
                quitting = True
                when = time.time() + self.close_wait

            if quitting and time.time() > when:
                self.log.debug('quitting')
                break

    def setup_tty(self):
        if os.isatty(sys.stdin.fileno()):
            logging.debug('putting tty into raw mode')
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin)

    def restore_tty(self):
        if os.isatty(sys.stdin.fileno()):
            logging.debug('restoring tty configuration')
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN,
                              self.old_settings)

    def handle_stdin(self, event):
        if event in (select.POLLHUP, select.POLLNVAL):
            logging.debug('event %d on stdin', event)

            logging.debug('eof on stdin')
            self.poll.unregister(sys.stdin)
            self.quit = True

        data = os.read(sys.stdin.fileno(), 1024)
        logging.debug('read %s (%d bytes) from stdin',
                       repr(data),
                       len(data))

        if not data:
            return

        if self.start_of_line and data == self.escape:
            self.read_escape = True
            return

        if self.read_escape and data == '.':
            logging.debug('exit by local escape code')
            raise UserExit()
        elif self.read_escape:
            self.read_escape = False
            self.ws.send(self.escape)

        self.ws.send(data)

        if data == '\r':
            self.start_of_line = True
        else:
            self.start_of_line = False

    def handle_websocket(self, event):
        if event in (select.POLLHUP, select.POLLNVAL):
            logging.debug('event %d on websocket', event)

            logging.debug('eof on websocket')
            self.poll.unregister(self.ws)
            self.quit = True

        data = self.ws.recv()
        logging.debug('read %s (%d bytes) from websocket from container',
                       repr(data),
                       len(data))
        if not data:
            return

        sys.stdout.write(data)
        sys.stdout.flush()

    def handle_resize(self,):
        """
        send the POST to resize the tty session size in container.
        curl -X POST -H "Content-Type: application/json" http://127.0.0.1:2375/containers/4b93a26d146e/resize?"h=40&w=180"

        Resize the container's PTY.

        If `size` is not None, it must be a tuple of (height,width), otherwise
        it will be determined by the size of the current TTY.
        """

        ## need to add here
        #if not self.israw():
        #    return

        size = self.tty_size(sys.stdout)

        if size is not None:
            rows, cols = size
            try:
                self.tty_resize(height=rows, width=cols)
            except IOError:  # Container already exited
                pass

    def tty_size(self, fd):
        """
        Return a tuple (rows,cols) representing the size of the TTY `fd`.

        The provided file descriptor should be the stdout stream of the TTY.

        If the TTY size cannot be determined, returns None.
        """

        if not os.isatty(fd.fileno()):
            return None

        try:
            dims = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, 'hhhh'))
        except:
            try:
                dims = (os.environ['LINES'], os.environ['COLUMNS'])
            except:
                return None

        return dims

    def tty_resize(self, height, width):
        # Ugly code style just for test. Will when in the future.
        hw = "h=" + str(height) + "&w=" + str(width)
        cmd = self.container.host_ip + "/containers/" + self.container.container_id + "/" + 'resize?"' + hw + '"'
        self.docker_cmd_send(cmd)

    def docker_cmd_send(self, cmd):
        """
        :param url: the http post Link
        :return:
        Just for test
        """

        cmd = 'curl -X POST -H "Content-Type: application/json" ' + "http://" + cmd
        os.system(cmd)

    def israw(self, **kwargs):
        """
        Returns True if the PTY should operate in raw mode.

        If the container was not started with tty=True, this will return False.
        """

        if self.raw is None:
            # Add POST to the container to get the size (need to talk to ZUN API-->Docker Daemon and return here)
            # For demo just using  POST to Docker Daemon
            #info = self._container_info()
            self.raw = sys.stdout.isatty() and info['Config']['Tty']

        return self.raw

class WINCHHandler(object):
    """
    WINCH Signal handler to keep the PTY correctly sized.
    """

    def __init__(self, client):
        """
        Initialize a new WINCH handler for the given PTY.

        Initializing a handler has no immediate side-effects. The `start()`
        method must be invoked for the signals to be trapped.
        """

        self.client = client
        self.original_handler = None

    def __enter__(self):
        """
        Invoked on entering a `with` block.
        """

        self.start()
        return self

    def __exit__(self, *_):
        """
        Invoked on exiting a `with` block.
        """

        self.stop()

    def start(self):
        """
        Start trapping WINCH signals and resizing the PTY.

        This method saves the previous WINCH handler so it can be restored on
        `stop()`.
        """

        def handle(signum, frame):
            if signum == signal.SIGWINCH:
                logging.debug("Send command to resize the tty session")
                size = self.client.handle_resize()



        self.original_handler = signal.signal(signal.SIGWINCH, handle)

    def stop(self):
        """
        Stop trapping WINCH signals and restore the previous WINCH handler.
        """

        if self.original_handler is not None:
            signal.signal(signal.SIGWINCH, self.original_handler)