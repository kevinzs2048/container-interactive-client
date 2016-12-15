class ContainerWebSocketException(Exception):
    'base for all ContainerWebSocket interactive generated exceptions'
    def __init__(self, wrapped=None):
        self.wrapped = wrapped

    def __str__(self):
        return '%s: %s' % (
            self.__doc__,
            self.wrapped if str(self.wrapped) else 'an unknown error occurred')

class UserExit(ContainerWebSocketException):
    'user requested disconnect'


class Disconnected(ContainerWebSocketException):
    'remote host closed connection'


class ConnectionFailed(ContainerWebSocketException):
    'failed to connect to remote host'