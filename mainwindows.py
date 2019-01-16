import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QDesktopWidget, QGridLayout, QLabel, QLineEdit,
                             QProgressBar, QTextEdit, QAction)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt


class MainWindows(QMainWindow):

    def __init__(self):
        super(QMainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        # mainwindows
        self.resize(600, 400)
        self.setFont(QFont('微軟正黑體', 14))
        self.center()
        self.setWindowTitle('楓林網影片下載軟體')

        # toolbar
        startAct = QAction(QIcon('start.png'), 'Start', self)
        startAct.triggered.connect(self.start_download)
        stopAct = QAction(QIcon('stop.png'), 'Stop', self)

        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(startAct)
        self.toolbar.addAction(stopAct)

        # statusbar
        self.statusbar = self.statusBar()
        self.statusbar.setFont(QFont('微軟正黑體', 8))

        self.progress_bar = QProgressBar(self.statusbar)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('0 %')
        self.progress_bar.setAlignment(Qt.AlignCenter)
        label_speed = QLabel('0 kb/s', self.statusbar)
        self.statusbar.addPermanentWidget(label_speed)
        self.statusbar.addWidget(self.progress_bar, 1)

        # widget
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        grid = QGridLayout()
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(10)
        self.widget.setLayout(grid)

        label_id = QLabel('ID: ', self)
        grid.addWidget(label_id, 0, 0)

        line_edit_id = QLineEdit(self)
        grid.addWidget(line_edit_id, 0, 1)

        self.text_edit_msg = QTextEdit(self)
        self.text_edit_msg.verticalScrollBar().rangeChanged.connect(self.scroll_to_button)
        self.text_edit_msg.setReadOnly(True)
        self.text_edit_msg.setPlainText('輸入ID後點擊開始下載。')
        grid.addWidget(self.text_edit_msg, 1, 0, 2, 2)

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

    def scroll_to_button(self):
        self.text_edit_msg.verticalScrollBar().setValue(self.text_edit_msg.verticalScrollBar().maximum())

    def start_download(self):
        print('downloading')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    windows = MainWindows()
    sys.exit(app.exec_())
