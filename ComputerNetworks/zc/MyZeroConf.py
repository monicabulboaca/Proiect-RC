import ipaddress
from typing import cast
from dns import DNSClasses
from dns.Cache_Local import *
from zc.Engine import Engine, Reaper
from zc.MyListener import Listener
from service.MyServiceInfo import *
from service.MyServiceBrowser import *
from dns.DNSClasses import _MDNS_ADDR, _MDNS_PORT, _GLOBAL_DONE, _TYPE_PTR, _CLASS_IN, _FLAGS_AA, _FLAGS_QR_QUERY, \
    _DNS_TTL, \
    _CHECK_TIME, _FLAGS_QR_RESPONSE, _TYPE_SRV, _TYPE_A, _TYPE_TXT, _REGISTER_TIME, _UNREGISTER_TIME, _TYPE_ANY, \
    _CLASS_UNIQUE
from zc.SocketFunctions import new_UDP_socket


class Zeroconf:
    def __init__(self):
        DNSClasses._GLOBAL_DONE = False
        self.listen_socket = new_UDP_socket()
        self.respond_sockets = []

        self.listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                      socket.inet_aton(_MDNS_ADDR) + socket.inet_aton('0.0.0.0'))

        respond_socket = new_UDP_socket()
        respond_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton('0.0.0.0'))
        self.respond_sockets.append(respond_socket)

        self.listeners = []
        self.browsers = []
        self.services = {}
        self.service_types = {}
        self.condition = threading.Condition()

        self.cache = Cache_Local()
        self.engine = Engine(self)
        self.listener = Listener(self)
        self.engine.add_reader(self.listener, self.listen_socket)
        self.reaper = Reaper(self)

    def wait(self, timeout):
        with self.condition:
            self.condition.wait(timeout / 1000)

    def notify_all(self):
        with self.condition:
            self.condition.notify_all()

    def get_service_info(self, type_, name, timeout=3000):
        info = ServiceInfo(type_, name)
        if info.request(self, timeout):
            return info
        return None

    def remove_service_listener(self, listener):
        for browser in self.browsers:
            if browser.listener == listener:
                browser.cancel()
                del browser

    def add_service_listener(self, type_, listener):
        self.remove_service_listener(listener)
        self.browsers.append(ServiceBrowser(self, type_, listener))

    def send(self, out, addr=_MDNS_ADDR, port=_MDNS_PORT):
        packet = out.packet()
        for socket_ in self.respond_sockets:
            if _GLOBAL_DONE:
                return
            if addr is None:
                real_addr = _MDNS_ADDR
            elif not cast(bool, ipaddress.ip_address(addr).version == 6
                            if socket_.family == socket.AF_INET6
                            else ipaddress.ip_address(
                                addr).version == 4
                         ):
                continue
            else:
                real_addr = addr
            bytes_sent = socket_.sendto(packet, 0, (real_addr, port))
            if bytes_sent != len(packet):
                raise Exception(
                    'Sent %d out of %d bytes!' % (bytes_sent, len(packet)))

    def check_service(self, info, allow_name_change=True):
        next_instance_number = 2
        instance_name = info.name[:-len(info.type_) - 1]
        now = current_time_millis()
        next_time = now
        j = 0
        while j < 3:
            for record in self.cache.entries_with_name(info.type_):
                if record.type_ == _TYPE_PTR and not record.is_expired(now) and record.alias == info.name:
                    if not allow_name_change:
                        raise Exception("NonUniqueNameException")
                    info.name = '%s-%s.%s' % (instance_name, next_instance_number, info.type_)
                    next_instance_number += 1
                    self.check_service(info)
                    return

            if now < next_time:
                self.wait(next_time - now)
                now = current_time_millis()
                continue

            out = DNSOutgoing(_FLAGS_QR_QUERY | _FLAGS_AA)
            self.debug = out
            out.add_question(DNSQuestion(info.type_, _TYPE_PTR, _CLASS_IN))
            out.add_authoritative_answer(DNSPointer(info.type_, _TYPE_PTR, _CLASS_IN,
                                                    _DNS_TTL, info.name))
            self.send(out)
            j += 1
            next_time += _CHECK_TIME

    def register_service(self, info, ttl=_DNS_TTL):
        self.check_service(info)
        self.services[info.name.lower()] = info
        if info.type_ in self.service_types:
            self.service_types[info.type_] += 1
        else:
            self.service_types[info.type_] = 1
        now = current_time_millis()
        next_time = now
        j = 0
        while j < 3:
            if now < next_time:
                self.wait(next_time - now)
                now = current_time_millis()
                continue
            out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
            out_.add_answer_at_time(
                DNSService(info.name, _TYPE_SRV, _CLASS_IN, ttl, info.priority,
                           info.weight, info.port, info.server), 0)
            self.send(out_)
            j += 1
            next_time += _REGISTER_TIME

    def unregister_service(self, info):
        try:
            del self.services[info.name.lower()]
            if self.service_types[info.type_] > 1:
                self.service_types[info.type_] -= 1
            else:
                del self.service_types[info.type_]
        except Exception as e:
            # print('Unknown error:%r', e)
            pass
        now = current_time_millis()
        next_time = now
        j = 0
        while j < 3:
            if now < next_time:
                self.wait(next_time - now)
                now = current_time_millis()
                continue
            out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
            out_.add_answer_at_time(DNSPointer(info.type_, _TYPE_PTR, _CLASS_IN, 0, info.name), 0)
            out_.add_answer_at_time(DNSService(info.name, _TYPE_SRV, _CLASS_IN, 0, info.priority,
                                               info.weight, info.port, info.server), 0)
            out_.add_answer_at_time(DNSText(info.name, _TYPE_TXT, _CLASS_IN, 0, info.text), 0)
            if info.address:
                out_.add_answer_at_time(
                    DNSAddress(info.server, _TYPE_A, _CLASS_IN, 0, info.address), 0)
            self.send(out_)
            j += 1
            next_time += _UNREGISTER_TIME

    def unregister_all_services(self):
        if len(self.services) > 0:
            now = current_time_millis()
            next_time = now
            j = 0
            while j < 3:
                if now < next_time:
                    self.wait(next_time - now)
                    now = current_time_millis()
                    continue
                out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                for info in self.services.values():
                    out_.add_answer_at_time(
                        DNSPointer(info.type_, _TYPE_PTR, _CLASS_IN, 0, info.name), 0)
                    out_.add_answer_at_time(
                        DNSService(info.name, _TYPE_SRV, _CLASS_IN, 0, info.priority,
                                   info.weight, info.port, info.server), 0)
                    out_.add_answer_at_time(
                        DNSText(info.name, _TYPE_TXT, _CLASS_IN, 0, info.text), 0)
                    if info.address:
                        out_.add_answer_at_time(
                            DNSAddress(info.server, _TYPE_A, _CLASS_IN, 0, info.address), 0)
                self.send(out_)
                j += 1
                next_time += _UNREGISTER_TIME

    def update_record(self, now, record):
        for listener in self.listeners:
            listener.update_record(self, now, record)
        self.notify_all()

    def add_listener(self, listener, question):
        now = current_time_millis()
        self.listeners.append(listener)
        if question is not None:
            for record in self.cache.entries_with_name(question.name):
                if question.answered_by(record) and not record.is_expired(now):
                    listener.update_record(self, now, record)
        self.notify_all()

    def remove_listener(self, listener):
        try:
            self.listeners.remove(listener)
            self.notify_all()
        except Exception as e:
            # print('Unknown error:%r', e)
            pass

    def handle_response(self, msg):
        now = current_time_millis()
        for record in msg.answers:
            expired = record.is_expired(now)
            if record in self.cache.entries():
                if expired:
                    self.cache.remove(record)
                else:
                    entry = self.cache.get(record)
                    if entry is not None:
                        entry.reset_TTL(record)
                        record = entry
            else:
                self.cache.add(record)
            self.update_record(now, record)

    def handle_query(self, msg, addr, port):
        out_ = None
        if port != _MDNS_PORT:
            out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA, False)
            for question in msg.questions:
                out_.add_question(question)

        for question in msg.questions:
            if question.type_ == _TYPE_PTR:
                if question.name == "_services._dns-sd._udp.local.":
                    for serv_type in self.service_types.keys():
                        if out_ is None:
                            out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                        out_.add_answer(msg,
                                        DNSPointer("_services._dns-sd._udp.local.",
                                                   _TYPE_PTR, _CLASS_IN, _DNS_TTL,
                                                   serv_type))

                for service in self.services.values():
                    if question.name == service.type_:
                        if out_ is None:
                            out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                        out_.add_answer(msg,
                                        DNSPointer(service.type_,
                                                   _TYPE_PTR, _CLASS_IN, _DNS_TTL,
                                                   service.name))
            else:
                try:
                    if out_ is None:
                        out_ = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                    if question.type_ in (_TYPE_A, _TYPE_ANY):
                        for service in self.services.values():
                            if service.server == question.name.lower():
                                out_.add_answer(msg,
                                                DNSAddress(question.name,
                                                           _TYPE_A,
                                                           _CLASS_IN | _CLASS_UNIQUE,
                                                           _DNS_TTL,
                                                           service.address))
                    service = self.services.get(question.name.lower(), None)
                    if not service:
                        continue

                    if question.type_ in (_TYPE_SRV, _TYPE_ANY):
                        out_.add_answer(msg, DNSService(question.name,
                                                        _TYPE_SRV,
                                                        _CLASS_IN | _CLASS_UNIQUE,
                                                        _DNS_TTL, service.priority, service.weight,
                                                        service.port, service.server))
                    if question.type_ in (_TYPE_TXT, _TYPE_ANY):
                        out_.add_answer(msg, DNSText(question.name,
                                                     _TYPE_TXT,
                                                     _CLASS_IN | _CLASS_UNIQUE,
                                                     _DNS_TTL, service.text))
                    if question.type_ == _TYPE_SRV:
                        out_.add_additional_answer(DNSAddress(service.server,
                                                              _TYPE_A,
                                                              _CLASS_IN | _CLASS_UNIQUE,
                                                              _DNS_TTL, service.address))

                except Exception as e:
                    # print('Unknown error: %r', e)
                    pass
        if out_ is not None and out_.answers:
            out_.id = msg.id
            self.send(out_, addr, port)

    def close(self):
        if not _GLOBAL_DONE:
            DNSClasses._GLOBAL_DONE = True
            self.notify_all()
            self.engine.notify()
            self.unregister_all_services()
            for socket_ in [self.listen_socket] + self.respond_sockets:
                socket_.close()


