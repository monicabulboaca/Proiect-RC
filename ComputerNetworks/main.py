import os
import re
import socket
import sys
import time
from collections import defaultdict

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog
from PyQt5.uic import loadUi
from service.FindServiceTypes import ZeroconfServiceTypes
from service.MyServiceInfo import ServiceInfo
from zc.MyZeroConf import Zeroconf
from service.MyServiceBrowser import ServiceBrowser


def verify_type(type):
    # print("type")
    comp = type.split(".")
    transport_protocol = ['_udp', '_tcp']
    if not type.endswith("local."):
        return False
    if not comp[1] in transport_protocol:
        return False
    if not comp[0][0] == '_':
        return False
    return True


def verify_name(name, type):
    # print("name")
    if type == '' or not name.endswith(type):
        return False
    return True


def verify_addr(addr):
    # print("addr")
    nr = 0
    comp = addr.split(".")
    if len(comp) != 4:
        return False
    for i in comp:
        if int(i) < 0 or int(i) >= 255:
            return False
        if int(i) == 255:
            nr = nr + 1
    if nr == 4:
        return False
    return True


def verify_port(port):
    # print("port")
    if not str(port).isnumeric():
        return False
    if port not in range(0, 65535):
        return False
    return True


def verify_weight(weight):
    # print("weight")
    if not str(weight).isnumeric():
        return False
    if weight not in range(0, 65535):
        return False
    return True


def verify_ttl(ttl):
    # print("ttl")
    if not str(ttl).isnumeric():
        return False
    return True


def verify_service(type, name, addr, port, weight, ttl):
    if verify_type(type):
        if verify_name(name, type):
            if verify_addr(addr):
                if verify_port(port):
                    if verify_weight(weight):
                        if verify_ttl(ttl):
                            return True
    return False


class Ui_MainWindow(QMainWindow):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        ui_path = os.path.join(self.ROOT_DIR, "ui/MainInterface.ui")
        loadUi(ui_path, self)

        self.errorPopUp = Ui_PopUpError(self)
        self.removeSRVPopUp = Ui_PopUpUnregisterSRV(self)
        self.addServicePopUp = Ui_PopUpAddService()
        self.connections = Connections(self, self.errorPopUp, self.removeSRVPopUp)

        self.btn_getIP.clicked.connect(self.connections.get_IP_address)
        self.btn_add_srv.clicked.connect(self.addServicePopUp.show)

        self.btn_remove_srv.setEnabled(False)
        self.btn_remove_srv.clicked.connect(self.removeSRVPopUp.show_and_set_text)
        self.removeSRVPopUp.btn_ok.clicked.connect(self.connections.unregister_service)
        self.removeSRVPopUp.btn_cancel.clicked.connect(self.removeSRVPopUp.hide)

        self.addServicePopUp.btn_ok.clicked.connect(self.connections.register_service)
        self.addServicePopUp.btn_cancel.clicked.connect(self.addServicePopUp.hide)

        self.btn_search_srv_types.clicked.connect(self.connections.find_services_types)
        self.btn_search_all_srv.setEnabled(False)
        self.btn_search_all_srv.clicked.connect(self.connections.search_srv_selected_type)

        self.btn_search_hostn_srv.setEnabled(False)
        self.btn_search_hostn_srv.clicked.connect(self.connections.search_hostnames_with_service)

        # self.addServicePopUp.input_type.setText("_xxxx._udp.local.")
        self.addServicePopUp.input_type.setText("_http._tcp.local.")
        self.addServicePopUp.input_type.setAlignment(QtCore.Qt.AlignCenter)

        # self.addServicePopUp.input_name.setText("Larisa._xxxx._udp.local.")
        self.addServicePopUp.input_name.setText("MONICA24 Web-based Configuration._http._tcp.local.")
        self.addServicePopUp.input_name.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_addr.setText("192.168.2.2")
        self.addServicePopUp.input_addr.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_addr.setText("192.168.2.2")
        self.addServicePopUp.input_addr.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_port.setText("278")
        self.addServicePopUp.input_port.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_weight.setText("20")
        self.addServicePopUp.input_weight.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_priority.setText("3")
        self.addServicePopUp.input_priority.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_ttl.setText("3000")
        self.addServicePopUp.input_ttl.setAlignment(QtCore.Qt.AlignCenter)

        self.addServicePopUp.input_server.setText("pop.local")
        self.addServicePopUp.input_server.setAlignment(QtCore.Qt.AlignCenter)


class Ui_PopUpAddService(QDialog):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        super(Ui_PopUpAddService, self).__init__()
        ui_path = os.path.join(self.ROOT_DIR, "ui/AddService.ui")
        loadUi(ui_path, self)
        self.btn_ok.clicked.connect(self.pressed_ok)
        self.info = []

    def pressed_ok(self):
        self.hide()


class Ui_PopUpError(QDialog):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, parent):
        super().__init__(parent=parent)
        ui_path = os.path.join(self.ROOT_DIR, "ui/PopUpError.ui")
        loadUi(ui_path, self)
        self.btn_ok.clicked.connect(self.pressed_ok)

    def pressed_ok(self):
        self.hide()


class Ui_PopUpUnregisterSRV(QDialog):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, parent):
        super().__init__(parent=parent)
        ui_path = os.path.join(self.ROOT_DIR, "ui/RemoveServicePopUp.ui")
        loadUi(ui_path, self)
        self.btn_ok.clicked.connect(self.pressed_ok)
        self.parent = parent

    def pressed_ok(self):
        self.hide()

    def show_and_set_text(self):
        if self.parent.connections.zeroConf is not None:
            index = self.parent.cbox_select_service.currentIndex()
            if int(index) != -1:
                self.show()
                service = self.parent.cbox_select_service.currentText()
                if service != "None":
                    self.show()
                    self.textEdit.setText("The service %s will be removed!" % str(service))
                else:
                    self.hide()
                    self.parent.errorPopUp.show()
                    self.parent.errorPopUp.textEdit.setText("Please select a service!")
        else:
            self.parent.errorPopUp.show()
            self.parent.errorPopUp.textEdit.setText("You can't unregister \n this service!")


class MyListener(object):

    def __init__(self):
        self.string = ""
        self.addr = []
        self.names = []
        self.info = []
        self.servers = []
        self.types = []
        self.all_info = []

    def remove_service(self, zeroconf, type, name):
        self.string = " "
        self.string += ("Service %s removed\n" % (name,))
        self.string += ('\n')
        self.all_info.append(self.string)

    def add_service(self, zeroconf, type, name):
        self.names.append(name)
        self.string = ""
        self.string += "Service %s added\n" % (name,)
        self.string += ("    Type is %s\n" % (type,))
        self.types.append(type)
        info = zeroconf.get_service_info(type, name)
        self.info.append(info)
        if info:
            self.string += ("    Address is %s:%d\n" % (socket.inet_ntoa(info.address),
                                                        info.port))
            self.addr.append(socket.inet_ntoa(info.address))

            self.string += ("    Weight is %d,\n    Priority is %d\n" % (info.weight,
                                                                         info.priority))
            self.string += ("    Server is %s\n" % info.server)
            self.servers.append(info.server)
            if info._properties:
                self.string += "    Properties are\n"
                for key, value in info._properties.items():
                    self.string += ("\t%s: %s\n" % (key, value))
        else:
            self.string += "    No info!\n"
        self.string += '\n'
        self.all_info.append(self.string)


class Connections:
    def __init__(self, mainWindow, errorWindow, unregWindow):
        self.info = []
        self.main_window = mainWindow
        self.err_window = errorWindow
        self.unreg_window = unregWindow
        self.zeroConf = None
        self.zeroConf2 = None
        self.browser = None
        self.listener = MyListener()
        self.servers = defaultdict(list)

    def get_IP_address(self):
        self.listener.names.clear()
        hostname = self.main_window.hostname.text()
        if hostname != "":
            if self.zeroConf is None:
                self.zeroConf = Zeroconf()
            self.main_window.output_display.append("Resolving hostname...")
            type_ = re.sub("^[^.]+", '', hostname)
            type_ = type_[1:]   # if hostname='Monica24.local' => type_ = 'local'
            try:
                browser = ServiceBrowser(self.zeroConf, type_, self.listener)
                time.sleep(3)
                browser.cancel()
            except:
                print("Error")
            # print(self.listener.addr)
            address = ''
            for n in range(len(self.listener.names)):
                if hostname == self.listener.names[n]:
                    address = self.listener.addr[n]
            self.main_window.output_display.append("\t" + address)
        else:
            self.main_window.errorPopUp.show()
            self.main_window.errorPopUp.textEdit.setPlainText("Please insert hostname!")

    def register_service(self):
        type = self.main_window.addServicePopUp.input_type.text()
        name = self.main_window.addServicePopUp.input_name.text()
        addr = self.main_window.addServicePopUp.input_addr.text()
        port = int(self.main_window.addServicePopUp.input_port.text())
        weight = int(self.main_window.addServicePopUp.input_weight.text())
        priority = self.main_window.addServicePopUp.input_priority.text()
        ttl = int(self.main_window.addServicePopUp.input_ttl.text())
        server = self.main_window.addServicePopUp.input_server.text()
        if verify_service(type, name, addr, port, weight, ttl):
            info = ServiceInfo(type_=type, name=name,
                               address=socket.inet_aton(addr), port=int(port),
                               weight=int(weight), priority=int(priority), properties={},
                               server=server)
            if self.zeroConf is None:
                self.zeroConf = Zeroconf()
            self.main_window.output_display.append("\nRegistering service '%s'" % name)
            self.zeroConf.register_service(info)
            self.main_window.output_display.append("\nService registered!")
            self.servers[server].append(name)
            idx = self.main_window.cbox_select_service_type.findText(type)
            if idx == -1:
                self.main_window.cbox_select_service_type.addItem(type)
            if self.main_window.cbox_select_service_type.currentText() == 'type':
                self.main_window.cbox_select_service.addItem(name)
        else:
            self.err_window.show()
            self.err_window.textEdit.setText("The service is incorrect!")

    def unregister_service(self):
            index = self.main_window.cbox_select_service.currentIndex()
            name = self.main_window.cbox_select_service.currentText()
            self.main_window.output_display.append("\nUnregistering of service '%s'" % name)
            self.main_window.cbox_select_service.removeItem(index)
            for i in range(len(self.listener.names)):
                if name == self.listener.names[i]:
                 self.zeroConf.unregister_service(self.listener.info[i])
            self.zeroConf.close()
            self.zeroConf = None
            self.main_window.output_display.append("\nService unregistered!")


    def find_services_types(self):
        if self.zeroConf2 is None:
            self.zeroConf2 = Zeroconf()
        service_types = ZeroconfServiceTypes.find(zc=self.zeroConf2, timeout=0.5)
        # print(service_types)
        self.main_window.output_display.append("Types of services:")
        self.main_window.cbox_select_service_type.clear()
        self.main_window.cbox_select_service_type.addItem("None")
        for serv in service_types:
            self.main_window.cbox_select_service_type.addItem(serv)
            self.main_window.output_display.append(f"   {serv}")
        self.main_window.output_display.append("\n")
        self.main_window.btn_search_all_srv.setEnabled(True)

    def search_srv_selected_type(self):
        self.main_window.cbox_select_service.clear()
        srv_type = self.main_window.cbox_select_service_type.currentText()
        if srv_type != 'None':
            if self.zeroConf2 is None:
                self.zeroConf2 = Zeroconf
            self.main_window.output_display.append("Browsing services...")
            self.browser = ServiceBrowser(self.zeroConf2, srv_type, self.listener)
            time.sleep(3)
            self.browser.cancel()
            # print(str(self.listener.string))
            self.main_window.cbox_select_service.addItem('None')
            for i in range(len(self.listener.info)):
                # print(self.listener.info[i])
                srv_name = str(self.listener.info[i]).split(",")[1].split("=")[1][1:-1]
                srv_server = str(self.listener.info[i]).split(",")[6].split("=")[1][1:-1]
                self.servers[srv_server].append(srv_name)
                if self.listener.types[i] == srv_type:
                    services = [self.main_window.cbox_select_service.itemText(i) for i in range(self.main_window.cbox_select_service.count())]
                    bad = 0
                    for s in services:
                        if s == self.listener.names[i]:
                            bad = 1
                            continue
                    if bad == 0:
                        self.main_window.cbox_select_service.addItem(self.listener.names[i])
                        self.main_window.output_display.append(self.listener.all_info[i])
            self.main_window.btn_remove_srv.setEnabled(True)
            self.main_window.btn_search_hostn_srv.setEnabled(True)
        else:
            self.err_window.show()
            self.err_window.textEdit.setText("Please select service type!")

    def search_hostnames_with_service(self):
        idx = self.main_window.cbox_select_service.currentIndex()
        if idx != -1:
            service_name = self.main_window.cbox_select_service.currentText()
            if service_name != "None":
                self.main_window.output_display.append("Servers with selected service are: ")
                for hosts in self.servers:
                    # print(hosts)
                    # print(self.servers[hosts])
                    # print('service_name = ' + str(service_name))
                    # print("service: " + str(self.servers[hosts][0]))
                    if service_name == str(self.servers[hosts][0]):
                        self.main_window.output_display.append("\t" + str(hosts))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.show()
    ui.raise_()
    sys.exit(app.exec_())

