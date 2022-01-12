from functools import reduce
from dns.DNSClasses import *

'''utilitate: pastrez intrarile local in memorie prin intermediul unei liste pe care o pot modifica adaugand elemente, memoria aceasta o folosesc in initializare la zeroconfig'''

class Cache_Local:
    def __init__(self):
        self.cache = {}

    def add(self, entry):
        self.cache.setdefault(entry.key, []).append(entry)

    def remove(self, entry):
        try:
            l = self.cache[entry.key]
            l.remove(entry)
            if not l:
                del self.cache[entry.key]
        except (KeyError, ValueError):
            pass

    def get(self, entry):
        try:
            l = self.cache[entry.key]
            return l[l.index(entry)]
        except (KeyError, ValueError):
            return None

    def get_by_details(self, name, type_, class_):
        entry = DNSEntry(name, type_, class_)
        return self.get(entry)

    def entries(self):
        if not self.cache:
            return []
        else:
            return reduce(lambda x, y: x + y, self.cache.values())

    def entries_with_name(self, name):
        try:
            return self.cache[name]
        except KeyError:
            return []