from dns.DNSIncoming import *
from dns.DNSClasses import *
from dns.DNSClasses import _MAX_MSG_ABSOLUTE, _MDNS_PORT, _MDNS_ADDR

'''
un Listener este folosit pentru a asculta pe grup-ul multicast  pe care mesajele DNS sunt trimise,
 permitand implementarii sa stocheze (cache) informatia care ajunge.
 Are nevoie de inregistrarea cu un obiect Engine pt a avea metoda read() apelata cand un socket este disponibil pt citire
'''


class Listener:
    def __init__(self, zeroconf):
        self.zeroconf = zeroconf
        self.data = None

    def handle_read(self, socket_):
        try:
            data, (addr, port) = socket_.recvfrom(_MAX_MSG_ABSOLUTE)
        except socket.error as err:
            if err.errno == socket.EBADF:
                return
            else:
                raise err
        self.data = data
        msg = DNSIncoming(data)
        if msg.is_query():
            if port == _MDNS_PORT:
                self.zeroconf.handle_query(msg, _MDNS_ADDR, _MDNS_PORT)
        else:
            self.zeroconf.handle_response(msg)
