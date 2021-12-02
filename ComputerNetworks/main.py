import os
import re
import socket
import sys
import time

from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog
from PyQt5.uic import loadUi
from zeroconf import Zeroconf
from MyServiceBrowser import ServiceBrowser
# from myzeroconf import MyZeroConf


class Ui_MainWindow(QMainWindow):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        ui_path = os.path.join(self.ROOT_DIR, "MainInterface.ui")
        loadUi(ui_path, self)

        self.connections = Connections(self)
        self.errorPopUp = Ui_PopUpError(self)
        self.addServicePopUp = Ui_PopUpAddService()
        self.btn_getIP.clicked.connect(self.connections.get_IP_address)
        self.btn_addSrv.clicked.connect(self.connections.register_service)
        self.comboBox_select.addItem("None")
        self.comboBox.addItem("None")


class Ui_PopUpAddService(QDialog):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        super(Ui_PopUpAddService, self).__init__()
        ui_path = os.path.join(self.ROOT_DIR, "AddService.ui")
        loadUi(ui_path, self)
        self.btn_ok.clicked.connect(self.pressed_ok)

    def pressed_ok(self):
        self.hide()


class Ui_PopUpError(QDialog):

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, parent):
        super().__init__(parent=parent)
        ui_path = os.path.join(self.ROOT_DIR, "PopUpError.ui")
        loadUi(ui_path, self)
        self.btn_ok.clicked.connect(self.pressed_ok)

    def pressed_ok(self):
        self.hide()


class MyListener:

    def __init__(self, hostname):
        self.string = ""
        self.hostname = hostname

    def remove_service(self, zeroconf, type, name):
        pass
        print(f'Service {name} removed')

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            if self.hostname == name:
                self.string += (f'{socket.inet_ntoa(info.address)}')
        else:
            self.string += "   No info!\n"


class Connections:
    def __init__(self, mainWindow):
        self.main_window = mainWindow
        self.zeroConf = None
        self.zeroConf2 = None

    def get_IP_address(self):
        hostname = self.main_window.ip_address.text()
        if hostname != "":
            if self.zeroConf2 is None:
                self.zeroConf2 = Zeroconf()

            self.main_window.outputDisplay.append("Resolving hostname...")
            listener = MyListener(hostname)
            type_ = re.sub("^[^.]+", '', hostname)
            type_ = type_[1:]

            browser = ServiceBrowser(self.zeroConf2, type_, listener)
            time.sleep(3)
            browser.cancel()
            self.main_window.ip_address.setText(listener.string)
            self.main_window.outputDisplay.append("\t"+listener.string)

        else:
            self.main_window.errorPopUp.show()
            self.main_window.errorPopUp.textEdit.setPlainText("Please insert hostname!")

    def register_service(self):
        self.main_window.addServicePopUp.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.show()
    ui.raise_()
    sys.exit(app.exec_())