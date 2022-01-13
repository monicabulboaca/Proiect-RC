import ipaddress
import socket
import struct
from typing import cast

_MDNS_PORT = 5353
_MDNS_ADDR = '192.168.0.1'


def new_UDP_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ttl = struct.pack(b'B', 255)
    loop = struct.pack(b'B', 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, loop)
    s.bind(('', _MDNS_PORT))
    return s


def can_send_to(sock: socket.socket, address: str) -> bool:
    addr = ipaddress.ip_address(address)
    return cast(bool, addr.version == 6 if sock.family == socket.AF_INET6 else addr.version == 4)
