import os
import sys
import time

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QRectF, QTimer, QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPalette

pipe_path = '/tmp/oneshot-pipe'

try: base_path = sys._MEIPASS
except AttributeError: base_path = os.path.abspath('.')

class WatchPipe(QThread):
    change_image = pyqtSignal(str)
    
    def run(self):
        while True:
            if os.path.exists(pipe_path): break
            else: time.sleep(0.1)

        pipe = open(pipe_path, 'r')
        pipe.flush()

        while True:
            message = os.read(pipe.fileno(), 256)
            if len(message) > 0:
                self.change_image.emit(message.decode())
            else:
                QCoreApplication.quit()

            time.sleep(0.05)
            
class Journal(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                
        self.label = QLabel(self)
        
        self.setWindowFlags(self.windowFlags())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.change_image('default')
        self.show()
        self.setMinimumSize(800, 600)
        self.setMaximumSize(800, 600)
        self.setGeometry(0, 0, 800, 600)
    
    def change_image(self, name):
        name = name.replace('_en', '')
        self.pixmap = QPixmap(os.path.join(base_path, 'images', '{}.png'.format(name)))
        self.label.setPixmap(self.pixmap)


class Niko(QWidget):
    def __init__(self, *args, **kwargs):
        self.start_x, self.start_y = kwargs['start_x'], kwargs['start_y']
        del kwargs['start_x'], kwargs['start_y']
        
        super().__init__(*args, **kwargs)

        self.label = QLabel(self)

        self.frames = [QPixmap(os.path.join(base_path, 'images', 'niko{}.png'.format(n))) for n in range(1,4)]
        self.drawNikoFrame(0)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowFlags( \
                Qt.FramelessWindowHint | \
                Qt.WindowStaysOnTopHint | \
                Qt.NoDropShadowWindowHint)
        self.show()

        self.setMinimumSize(24 * 2, 32 * 2)
        self.setMaximumSize(24 * 2, 32 * 2)
        self.setGeometry(self.start_x, self.start_y, 24 * 2, 32 * 2)

    def update(self, y):
        offset = self.start_y - y
        self.drawNikoFrame(offset)
        self.move(self.start_x, y)

    def drawNikoFrame(self, offset):
        if offset % 32 >= 16:
            frame = 1
        elif (offset // 32) % 2 == 1:
            frame = 0
        else:
            frame = 2

        self.label.setPixmap(self.frames[frame])


class NikoThread(QThread):
    update = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        self.y, self.screen_y = kwargs['start_y'], kwargs['screen_y']
        del kwargs['start_y'], kwargs['screen_y']
        super().__init__(*args, **kwargs)


    def run(self):
        while True:
            self.y += 2
            if (self.y > self.screen_y):
                break

            self.update.emit(self.y)
            time.sleep(1 / 60)

        QCoreApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) == 3:
        # "Niko-leaves-the-screen" mode
        x, y = int(sys.argv[1]), int(sys.argv[2])
        niko = Niko(start_x=x, start_y=y)

        thread = NikoThread(start_y=y, screen_y=app.primaryScreen().size().height())
        thread.update.connect(niko.update)
        thread.start()
    else:
        # Author's Journal mode
        journal = Journal()
    
        thread = WatchPipe()
        thread.change_image.connect(journal.change_image)
        thread.start()
    
    app.exec_()
