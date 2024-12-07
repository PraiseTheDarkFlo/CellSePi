
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget
import sys
from .. import GUI
from ...CellSePi import CellSePi


# PyQt-Fenster definieren
class MyQtWindow(QWidget):
    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        print(csp.bit_depth)
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
def open_qt_window(csp: CellSePi):
    app = QApplication(sys.argv)
    window = MyQtWindow(csp)
    window.show()
    app.exec()