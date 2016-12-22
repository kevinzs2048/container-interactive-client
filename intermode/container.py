import logging
import os
import sys
class Container (object):
    def __init__(self, host_ip, container_id, remote_api_ver):
        self.container_id = container_id
        self.host_ip = host_ip
        self.remote_api_ver = remote_api_ver