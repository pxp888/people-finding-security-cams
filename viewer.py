from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QSound

import cv2
import multiprocessing as mp
import threading
import pickle
import time
import datetime
import pytz
import PIL
import os
import sys
import numpy as np
import time
import msgpack
import zmq


while True:
    filpath = 'config.txt'
    if os.path.exists(filpath): break
    filpath = '/home/config.txt'
    if os.path.exists(filpath): break
    filpath = '/home/pxp/Desktop/engine/config.txt'
    if os.path.exists(filpath): break
    print('No configuration found')
    quit()

sources = []
camserver = "tcp://localhost:5557"
dataserver = "tcp://localhost:5556"

fil = open(filpath,'r')
sor = fil.read().split('\n')
fil.close()
for i in sor:
    n = i.split(': ')
    if n[0]=='camserver':
        camserver=n[1]
    if n[0]=='dataserver':
        dataserver=n[1]

print(filpath)
print(camserver)
print(dataserver)


class ring_link:
    def __init__(self, data):
        self.next = self
        self.data = data

class ring:
    def __init__(self,maxcount=720):
        self.end = None
        self.pos = None
        self.len = 0
        self.max = maxcount

    def add(self,data):
        if self.len==self.max:
            self.end.next.data = data
            self.end = self.end.next
        else:
            n = ring_link(data)
            self.len+=1
            if self.len==1:
                self.end = n
                self.pos = n
            else:
                n.next = self.end.next
                self.end.next = n
                self.end = n

    def step(self):
        if self.pos == None: return None
        self.pos = self.pos.next
        return self.pos.data

def human(t=0):
    if t==0: t = time.time()
    a = datetime.datetime.fromtimestamp(t)
    b = a.astimezone(pytz.timezone("Asia/Manila"))
    n = b.strftime("%y-%m-%d %H:%M:%S")
    return str(n)


class picthread(QThread):
    image = pyqtSignal(object,object)
    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(camserver)
        socket.setsockopt(zmq.SUBSCRIBE, b'p')
        while True:
            topic = socket.recv_string()
            idn,frame,mvmt = socket.recv_pyobj()
            frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
            self.image.emit(idn,frame)
            # if idn==0: print(idn,mvmt)
            if self.xx.value==1:
                socket.close()
                context.term()
                self.quit()

class datathread(QThread):
    info = pyqtSignal(object)
    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(dataserver)
        socket.setsockopt(zmq.SUBSCRIBE, b'd')
        while True:
            topic = socket.recv_string()
            m = socket.recv_pyobj()
            self.info.emit(m)
            if self.xx.value==1:
                socket.close()
                context.term()
                self.quit()

class viewer(QLabel):
    maxim = pyqtSignal(object)
    def __init__(self, idn, parent=None):
        super(viewer, self).__init__(parent)
        self.setScaledContents(True)
        self.setMinimumSize(1,1)
        self.mouseReleaseEvent = self.clicktest
        self.idn = idn
        self.mode = 0

        self.qin = mp.Queue()
        self.loop = ring(720)
        self.rec = False
        self.cut = 0
        self.lastinfo = 0
        self.alarm = 0

        self.tim = QTimer()
        self.tim.setInterval(75)
        self.tim.timeout.connect(self.beat)
        self.tim.start()

    def clicktest(self,n):
        pos = 0
        w = self.width()/3
        if n.pos().x() > w: pos+=1
        if n.pos().x() > w*2: pos+=1
        if pos==0:
            if self.mode==0:
                self.mode=1
                self.black()
            else:
                self.mode=0
        if pos==1:
            # print('vmax',self.idn)
            self.maxim.emit(self.idn)
        if pos==2:
            if self.mode==1:
                self.loop = ring(720)
                self.alarm.value = 0
                self.black()

    def black(self):
        nim = np.zeros((480,640,3),dtype=np.uint8)
        qimage = QImage(nim, nim.shape[1], nim.shape[0],QImage.Format_BGR888)
        pixmap = QPixmap(qimage)
        self.setPixmap(pixmap)

    def recvinfo(self,m):
        if not m[0]==self.idn: return
        tim = time.time()
        self.lastinfo = tim
        label = m[2]
        if 'person' in label:
            self.cut = tim + 10
            if not self.rec:
                self.alarm.value=1
                self.rec = True
                while True:
                    try:
                        image,tim = self.qin.get(False)
                        self.loop.add((image,tim))
                    except:
                        break
        if tim > self.cut:
            self.rec = False

    def recvimage(self,idn,image):
        if not idn==self.idn: return
        tim = time.time()
        if self.mode==0:
            self.display(image,tim)
        # if self.mode==1:
        if self.rec:
            self.loop.add((image,tim))
        else:
            self.qin.put((image,tim))
            while self.qin.qsize()>36:
                self.qin.get()

    def beat(self):
        if self.mode==0: return
        if self.loop.len==0: return
        image,tim = self.loop.step()
        self.display(image,tim)

    def display(self,im,tim=0):
        # nim = cv2.imdecode(np.frombuffer(nim, dtype='uint8'), -1)
        nim = np.flip(im,2).copy()
        if self.mode==0:
            cv2.putText(nim, human(tim), (20,30), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 1)
        else:
            cv2.putText(nim, human(tim), (20,30), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 0), 1)
        if self.lastinfo +3 < tim:
            cv2.putText(nim, 'OFFLINE', (20,60), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 1)
        qimage = QImage(nim, nim.shape[1], nim.shape[0],QImage.Format_RGB888)
        pixmap = QPixmap(qimage)
        self.setPixmap(pixmap)

class mainwin(QMainWindow):
    def __init__(self, parent=None):
        super(mainwin, self).__init__(parent)

        self.setWindowTitle('Watcher')
        frame = QFrame()
        self.setCentralWidget(frame)
        layout = QGridLayout()
        frame.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.resize(600,400)

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)

        self.alarm = mp.Value('i',0)
        self.t1 = picthread(self)
        self.t2 = datathread(self)
        self.xx = mp.Value('i',0)
        self.t1.xx = self.xx
        self.t2.xx = self.xx
        self.views = []
        idn = 0
        for i in range(4):
            vw = viewer(idn)
            vw.alarm = self.alarm
            vw.maxim.connect(self.maxim)
            self.views.append(vw)
            layout.addWidget(vw,int(idn/2),idn%2)
            self.t1.image.connect(vw.recvimage)
            self.t2.info.connect(vw.recvinfo)
            idn +=1

        self.t1.start()
        self.t2.start()

        self.tim = QTimer()
        self.tim.setInterval(1000)
        self.tim.timeout.connect(self.beat)
        self.tim.start()
        slist = ['m1.wav','sounds/m1.wav','/home/pxp/Desktop/engine/sounds/m1.wav']
        for i in slist:
            if os.path.exists(i):
                self.sound1 = i

        self.max = -1

    def maxim(self, n):
        # print('mainmax',n)
        if self.max==-1:
            self.max=n
            for i in range(len(self.views)):
                if n==i:
                    self.views[i].show()
                else:
                    self.views[i].hide()
        else:
            self.max=-1
            for i in self.views:
                i.show()

    def beat(self):
        pass
        # if self.alarm.value==1:
        #     QSound.play(self.sound1)
            # print('ALARM',human())

    def closeEvent(self, event):
        self.xx.value=1
        time.sleep(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = mainwin()
    form.show()
    # form.showFullScreen()
    form.showMaximized()
    form.raise_()
    app.exec_()
