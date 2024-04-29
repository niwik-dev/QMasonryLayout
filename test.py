from PySide6.QtCore import Qt

from layout.masonry import QMasonryFlowLayout, HAdapt, VExpand

import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
import random


class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._layout = QMasonryFlowLayout()
        self._layout.hAdapt = HAdapt.AutoZoom
        self._layout.vExpand = VExpand.HeightBalance
        self._layout.setColumnWidth(150)
        self.setLayout(self._layout)
        for i in range(20):
            label = QLabel()
            label.setFixedHeight(random.randint(50, 200))
            label.setFixedWidth(150)
            label.setStyleSheet(f"""
                background-color:rgb({random.randint(0, 255)}, {255}, {random.randint(0, 255)})
            """)
            self._layout.addWidget(label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = TestWidget()
    widget.show()
    sys.exit(app.exec())
