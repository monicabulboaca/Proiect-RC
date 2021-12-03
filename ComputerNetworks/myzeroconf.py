
import DNSClasses
from SocketFunctions import *

class MyZeroConf:
    def __init__(self):
        DNSClasses._GLOBAL_DONE = False
        self._listen_socket = new_socket()
