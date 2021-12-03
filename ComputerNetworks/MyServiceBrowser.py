import threading
from DNSClasses import *
import DNSClasses


class ServiceBrowser(threading.Thread):
    def __init__(self, zeroconf, type_, listener):
        super().__init__()
        self.zeroconf = zeroconf
        self.type_ = type_
        self.listener = listener
        self.services = {}
        self.next_time = current_time_millis()
        self.delay = DNSClasses._BROWSER_TIME
        self.list = []
        self.done = False
        self.zeroconf.add_listener(self, DNSQuestion(self.type_, DNSClasses._TYPE_PTR, DNSClasses._CLASS_IN))
        self.start()

    def cancel(self):
        self.done = True
        self.zeroconf.notify_all()

    def run(self):
        pass
