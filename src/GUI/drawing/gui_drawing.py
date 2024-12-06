import flet as ft
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget
import threading
import sys

# PyQt-Fenster definieren
class MyQtWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Window")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        label = QLabel("Hello from PyQt!")
        button = QPushButton("Close Window")
        button.clicked.connect(self.close)

        layout.addWidget(label)
        layout.addWidget(button)
        self.setLayout(layout)

# Funktion, um das PyQt-Fenster zu starten
def open_qt_window():
    app = QApplication(sys.argv)
    window = MyQtWindow()
    window.show()
    app.exec()