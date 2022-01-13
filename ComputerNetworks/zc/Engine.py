import select
import threading
from dns.DNSClasses import current_time_millis
from dns.DNSClasses import _GLOBAL_DONE

"""An engine wraps read access to sockets, allowing objects that
    need to receive data from sockets to be called back when the
    sockets are ready.
    A reader needs a handle_read() method, which is called when the socket
    it is interested and is ready for reading.
    Writers are not implemented here, because we only send short
    packets.
"""


class Engine(threading.Thread):
    def __init__(self, zeroconf):
        super().__init__()
        self.daemon = True
        self.zeroconf = zeroconf
        self.readers = {}
        self.timeout = 5
        self.condition = threading.Condition()
        self.start()

    def add_reader(self, reader, socket_):
        with self.condition:
            self.readers[socket_] = reader
            self.condition.notify()

    def get_readers(self):
        with self.condition:
            result = self.readers.keys()
            self.condition.notify()
        return result

    def delete_reader(self, socket_):
        with self.condition:
            del self.readers[socket_]
            self.condition.notify()

    def run(self):
        while not _GLOBAL_DONE:
            result = self.get_readers()
            if len(result) == 0:

                with self.condition:
                    self.condition.wait(self.timeout)
            else:
                try:
                    rr, wr, er = select.select(result, [], [], self.timeout)
                    for socket_ in rr:
                        try:
                            self.readers[socket_].handle_read(socket_)
                        except Exception as e:
                            # print('Unknown error:%r', e)
                            pass
                except Exception as e:
                    # print('Unknown error:%r', e)
                    pass

    def notify(self):
        with self.condition:
            self.condition.notify()


"""A Reaper is used by this module to remove cache entries that
    have expired.
"""


class Reaper(threading.Thread):
    def __init__(self, zeroconf):
        super().__init__()
        self.daemon = True
        self.zeroconf = zeroconf
        self.start()

    def run(self):
        while True:
            self.zeroconf.wait(10 * 1000)
            if _GLOBAL_DONE:
                return
            now = current_time_millis()
            for record in self.zeroconf.cache.entries():
                if record.is_expired(now):
                    self.zeroconf.update_record(now, record)
                    self.zeroconf.cache.remove(record)


