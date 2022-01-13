from service.MyServiceBrowser import *
from zc.MyZeroConf import Zeroconf


class ZeroconfServiceTypes:
    def __init__(self) -> None:
        self.found_services = set()

    def add_service(self, zc, type_, name):
        self.found_services.add(name)

    @classmethod
    def find(cls, zc=None, timeout=5.0):
        local_zc = zc or Zeroconf()
        listener = cls()
        browser = ServiceBrowser(local_zc, "_services._dns-sd._udp.local.", listener=listener)
        time.sleep(timeout)  # wait for responses
        if zc is None:  # close down anything we opened
            local_zc.close()
        else:
            browser.cancel()
        return tuple(sorted(listener.found_services))


if __name__ == '__main__':
    service_types = ZeroconfServiceTypes.find(timeout=0.5)
    print(service_types)
