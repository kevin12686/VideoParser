import os
import sys
import time
import re
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QDesktopWidget, QGridLayout, QLabel, QLineEdit,
                             QProgressBar, QTextEdit, QAction)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class Parser_Thread(QThread):
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
              'Accept-Encoding': 'gzip, deflate',
              'Referer': '',
              'Connection': 'keep-alive',
              'Upgrade-Insecure-Requests': '1',
              'Pragma': 'no-cache',
              'Cache-Control': 'no-cache'}

    name_re_module = re.compile(r'<title>(?P<name>.+) \| 楓林網</title>')
    m3u8_re_module = re.compile(r'php\?url=(?P<url>.+)\.m3u8')
    index_re_module = re.compile(r'url:\'(?P<url>.+)\',')
    video_re_module = re.compile(r'.*.ts')
    video_m3u8_re_module = re.compile(r'.+\.m3u8')
    http_re_module = re.compile(r'^http://.*')
    ts_re_module = re.compile(r'/(?P<ts_name>[^/]+)\.ts')

    page_url = 'http://8maple.ru/'
    m3u8_url = 'http://video.8maple.ru/m3u82/?url='

    limit_word = '\/:*?"\'><|'

    buffer_size = 10240

    id = ''
    run_flag = False
    set_max = pyqtSignal(int)
    update = pyqtSignal(int)
    speed = pyqtSignal(int)
    logging = pyqtSignal(str)
    thread_stop = pyqtSignal()

    def __init__(self):
        super(QThread, self).__init__()

    def __del__(self):
        self.wait()

    def download_start(self, video_id):
        self.id = video_id
        self.start()

    def run(self):
        self.run_flag = True
        self.set_max.emit(100)

        init_session = requests.session()
        header = dict(self.header)
        page_url = self.page_url
        video_id = self.id
        page_url += video_id + '/'

        page_result = init_session.get(url=page_url, headers=header)
        header.update(Referer=page_url)
        name = self.name_re_module.search(string=page_result.text)
        if '404 未找到' in page_result.text or name is None:
            self.logging.emit('** 找無此影片')
        else:
            name = name.group('name')
            for word in self.limit_word:
                if word in name:
                    name = name.replace(word, '')
            self.logging.emit('** 影集名稱: {}'.format(name))

            target_url = None
            for each in self.m3u8_re_module.finditer(string=page_result.text):
                index_url = self.m3u8_url + each.group('url')
                url_result = init_session.get(url=index_url, headers=header)
                search_url = self.index_re_module.search(string=url_result.text).group('url')
                if '.m3u8' in search_url:
                    target_url = search_url[:search_url.index('.m3u8') + 5]
                    break
            if target_url is None or index_url is None:
                self.logging.emit('** 下載失敗影片')
            else:
                header.update(Referer=index_url)

                directory = os.path.join(os.path.abspath(os.curdir), name)

                self.logging.emit('** 建立資料夾: {}'.format(name))

                if not os.path.exists(directory):
                    os.mkdir(directory)

                flag = True
                while flag:
                    m3u8_data = init_session.get(url=target_url, headers=header).content
                    ts_list = self.video_re_module.findall(string=m3u8_data.decode())
                    header.update(Referer=target_url)
                    if len(ts_list) == 0:
                        m3u8_place = self.video_m3u8_re_module.search(string=m3u8_data.decode()).group()
                        target_url = target_url.replace('index.m3u8', m3u8_place)
                    else:
                        flag = False
                m3u8_file = os.path.join(directory, name + '.m3u8')
                with open(m3u8_file, 'wb') as f:
                    f.write(m3u8_data)

                self.logging.emit('** 已抓取m3u8檔案')

                self.logging.emit('** 開始下載影片')

                ts_dir = os.path.join(directory, 'ts_file')
                if not os.path.exists(ts_dir):
                    os.mkdir(ts_dir)

                count = 0
                start = False
                with open(os.path.join(directory, name + '.mp4'), 'ab') as f:
                    for line in ts_list:
                        if not self.run_flag:
                            break

                        if self.video_re_module.match(string=line):
                            if not self.http_re_module.match(string=line):
                                line = target_url.replace('index.m3u8', line)

                            count += 1
                            ts_video_name = self.ts_re_module.search(string=line).group('ts_name')
                            if not os.path.exists(os.path.join(ts_dir, ts_video_name + '.ts')):

                                start = time.clock()
                                data = init_session.get(url=line, headers=header)

                                fault_counter = 0

                                while fault_counter < 10:
                                    try:
                                        with open(os.path.join(ts_dir, ts_video_name + '.ts'), 'wb') as ts_f:
                                            for ch in data.iter_content(chunk_size=self.buffer_size):
                                                f.write(ch)
                                                ts_f.write(ch)
                                            f.flush()
                                    except IOError:
                                        fault_counter += 1
                                if fault_counter >= 10:
                                    self.logging.emit('** 下載失敗影片')
                                    break
                                else:
                                    self.speed.emit(len(data.content) / time.clock() - start)

                            if not start and count > 5:
                                os.startfile(os.path.join(directory, name + '.mp4'))
                                start = True

                            self.update.emit(count * 100 / len(ts_list))

                if self.run_flag:
                    self.logging.emit('** 下載完成')
                else:
                    self.logging.emit('** 停止下載')
        self.thread_stop.emit()


class MainWindows(QMainWindow):

    def __init__(self):
        super(QMainWindow, self).__init__()
        self.parser = Parser_Thread()
        self.parser.set_max.connect(self.set_progress_max)
        self.parser.update.connect(self.update_progress)
        self.parser.logging.connect(self.logging)
        self.parser.thread_stop.connect(self.release_start_opa)
        self.initUI()

    def initUI(self):
        # mainwindows
        self.resize(600, 400)
        self.setFont(QFont('微軟正黑體', 14))
        self.center()
        self.setWindowTitle('楓林網影片下載軟體')

        # toolbar
        self.startAct = QAction(QIcon('start.png'), 'Start', self)
        self.startAct.triggered.connect(self.start_download)
        self.stopAct = QAction(QIcon('stop.png'), 'Stop', self)
        self.stopAct.setEnabled(False)
        self.stopAct.triggered.connect(self.stop_download)

        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(self.startAct)
        self.toolbar.addAction(self.stopAct)

        # statusbar
        self.statusbar = self.statusBar()
        self.statusbar.setFont(QFont('微軟正黑體', 8))

        self.progress_bar = QProgressBar(self.statusbar)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('0 %')
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.label_speed = QLabel('0 kb/s', self.statusbar)
        self.statusbar.addPermanentWidget(self.label_speed)
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

        self.line_edit_id = QLineEdit(self)
        grid.addWidget(self.line_edit_id, 0, 1)

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
        self.line_edit_id.setReadOnly(True)
        self.startAct.setEnabled(False)
        self.stopAct.setEnabled(True)
        self.parser.download_start(self.line_edit_id.text())

    def stop_download(self):
        self.parser.run_flag = False

    def release_start_opa(self):
        self.stopAct.setEnabled(False)
        self.line_edit_id.setReadOnly(False)
        self.startAct.setEnabled(True)

    def logging(self, data):
        self.text_edit_msg.setPlainText(self.text_edit_msg.toPlainText() + os.linesep + data)

    def set_progress_max(self, data):
        self.progress_bar.setMaximum(data)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat('{} %'.format(value))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    windows = MainWindows()
    sys.exit(app.exec_())
