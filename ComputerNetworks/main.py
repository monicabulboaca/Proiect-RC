from PyQt5 import QtCore, QtGui, QtWidgets
import socket
from zeroconf import ServiceBrowser, Zeroconf
from threading import Thread

hostname = ""
zeroConf = None
hostNamesList = []

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.resize(1060, 750)
        MainWindow.setStyleSheet("background-color: rgb(62, 62, 62);")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(40, 40, 401, 161))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.label_hostname = QtWidgets.QLabel(self.frame)
        self.label_hostname.setGeometry(QtCore.QRect(0, 0, 181, 41))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label_hostname.setFont(font)
        self.label_hostname.setStyleSheet("color: rgb(255, 255, 255);")

        self.input_hostname = QtWidgets.QLineEdit(self.frame)
        self.input_hostname.setGeometry(QtCore.QRect(170, 10, 231, 31))
        self.input_hostname.setStyleSheet("background-color: rgb(255, 255, 255);\n"
                                          "color: rgb(0, 0, 0);")

        self.btn_getIP = QtWidgets.QPushButton(self.frame)
        self.btn_getIP.setGeometry(QtCore.QRect(270, 132, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_getIP.setFont(font)
        self.btn_getIP.setStyleSheet("background-color: rgb(209, 209, 209);")
        self.btn_getIP.clicked.connect(self.get_IP_address)

        self.btn_getAllHostnames = QtWidgets.QPushButton(self.frame)
        self.btn_getAllHostnames.setGeometry(QtCore.QRect(100, 70, 221, 31))
        self.btn_getAllHostnames.setStyleSheet("background-color: rgb(209, 209, 209);")
        self.btn_getAllHostnames.clicked.connect(self.thread_hostnames)

        self.comboBox_allHostnames = QtWidgets.QComboBox(self.frame)
        self.comboBox_allHostnames.setGeometry(QtCore.QRect(0, 130, 261, 31))
        self.comboBox_allHostnames.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.comboBox_allHostnames.addItem("None")

        self.frame_2 = QtWidgets.QFrame(self.centralwidget)
        self.frame_2.setGeometry(QtCore.QRect(40, 500, 401, 161))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)

        self.label_selectSrv = QtWidgets.QLabel(self.frame_2)
        self.label_selectSrv.setGeometry(QtCore.QRect(10, 20, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_selectSrv.setFont(font)
        self.label_selectSrv.setStyleSheet("color: rgb(255, 255, 255);")

        self.btn_search_hostn = QtWidgets.QPushButton(self.frame_2)
        self.btn_search_hostn.setGeometry(QtCore.QRect(100, 70, 151, 31))
        self.btn_search_hostn.setStyleSheet("background-color: rgb(209, 209, 209);")

        self.comboBox_select = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_select.setGeometry(QtCore.QRect(150, 20, 231, 31))
        self.comboBox_select.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.comboBox_select.addItem("None")

        self.outputDisplay = QtWidgets.QTextEdit(self.centralwidget)
        self.outputDisplay.setGeometry(QtCore.QRect(450, 40, 590, 670))
        self.outputDisplay.setAutoFillBackground(False)
        self.outputDisplay.setStyleSheet("font: 11pt \"MS Shell Dlg 2\";\n"
            "color: rgb(255, 255, 0);\n"
            "border-color: rgb(0, 0, 0);\n"
            "background-color: rgb(35, 35, 35);")

        self.frame_3 = QtWidgets.QFrame(self.centralwidget)
        self.frame_3.setGeometry(QtCore.QRect(40, 240, 401, 201))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)

        self.btn_addSrv = QtWidgets.QPushButton(self.frame_3)
        self.btn_addSrv.setGeometry(QtCore.QRect(20, 40, 121, 41))
        self.btn_addSrv.setStyleSheet("background-color: rgb(209, 209, 209);")

        self.btn_removeSrv = QtWidgets.QPushButton(self.frame_3)
        self.btn_removeSrv.setGeometry(QtCore.QRect(20, 100, 121, 41))
        self.btn_removeSrv.setStyleSheet("background-color: rgb(209, 209, 209);")
        self.btn_removeSrv.setObjectName("btn_removeSrv")

        self.comboBox_ar = QtWidgets.QComboBox(self.frame_3)
        self.comboBox_ar.setGeometry(QtCore.QRect(150, 70, 231, 31))
        self.comboBox_ar.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.comboBox_ar.addItem("None")

        self.btn_searchSrv = QtWidgets.QPushButton(self.frame_3)
        self.btn_searchSrv.setGeometry(QtCore.QRect(100, 160, 161, 41))
        self.btn_searchSrv.setStyleSheet("background-color: rgb(209, 209, 209);")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_hostname.setText(_translate("MainWindow", "Configure hostname:"))
        self.btn_getIP.setText(_translate("MainWindow", "Get IP Address"))
        self.label_selectSrv.setText(_translate("MainWindow", "Select Service"))
        self.btn_search_hostn.setText(_translate("MainWindow", "Search hostnames"))
        self.btn_getAllHostnames.setText(_translate("MainWindow", "Get all hostnames from .local domain"))
        self.btn_addSrv.setText(_translate("MainWindow", "Add Service"))
        self.btn_removeSrv.setText(_translate("MainWindow", "Remove Service"))
        self.btn_searchSrv.setText(_translate("MainWindow", "Search All Services"))

    def get_hostname(self):
        global hostname
        hostname = self.input_hostname.text()
        print(self.input_hostname.text())

    def get_IP_address(self):
        hostname = self.comboBox_allHostnames.currentText()
        if hostname != " ":
            try:
                ip = str(socket.gethostbyname(hostname))
                self.outputDisplay.append(ip)
            except:
                pass


    def get_all_hostnames(self, i):
        global hostNamesList
        try:
            hostNamesList.append(socket.gethostbyaddr("192.168.0.%s" % str(i))[0])
        except:
            pass


    def thread_hostnames(self):
        for i in range(256):
            worker = Thread(target=self.get_all_hostnames, args=(i,))
            worker.start()
            worker.join(timeout=0.05)
            self.comboBox_allHostnames.addItem(hostNamesList[i])
        self.outputDisplay.append(str(hostNamesList))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    MainWindow.setWindowTitle("Aplicație de tip Zero-config bazată pe mDNS și DNS-SD")
    sys.exit(app.exec_())
