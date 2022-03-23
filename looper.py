from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import socket
import threading
import time
import os
import sys
import multiprocessing as mp
import zmq
import numpy as np
import cv2
import datetime
import pytz

#-------------------------------------SETUP VARIABLES
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
controlleraddress = "tcp://localhost:5558"

fil = open(filpath,'r')
sor = fil.read().split('\n')
fil.close()
for i in sor:
    n = i.split(': ')
    if n[0]=='camserver':
        camserver=n[1]
    if n[0]=='dataserver':
        dataserver=n[1]
    if n[0]=='controller':
        controlleraddress = n[1]
#-------------------------------------SETUP COMPLETE


def human(t=0):
    if t==0: t = time.time()
    a = datetime.datetime.fromtimestamp(t)
    b = a.astimezone(pytz.timezone("Asia/Manila"))
    n = b.strftime("%y-%m-%d %H:%M:%S")
    return str(n)




class looper:
    def __init__(self):
        self.loop = []
        self.end = 0
        self.pos = 0
        self.cut = 0
        self.lock = mp.Lock()

    def add(self, im, stat):
        tim = time.time()

        if stat==1:
            self.put(im)
            self.cut = tim+2
        else:
            if tim < self.cut:
                self.put(im)

    def put(self,im):
        self.lock.acquire()
        if len(self.loop)<720:
            self.loop.append(im)
        else:
            self.loop[self.end]=im
            self.end = (self.end+1)%720
        self.lock.release()

    def step(self):
        self.pos = (self.pos+1)%len(self.loop)
        return self.loop[self.pos]


def listen(state, loops):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(camserver)
    socket.setsockopt(zmq.SUBSCRIBE, b'p')
    while True:
        topic = socket.recv_string()
        idn,frame,mvmt = socket.recv_pyobj()
        frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
        cv2.putText(frame, human(time.time()), (20,30), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 1)

        loops[idn].add(frame,state[idn].value)

def datalisten(state):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(dataserver)
    socket.setsockopt(zmq.SUBSCRIBE, b'd')
    while True:
        topic = socket.recv_string()
        idn,bbox,label,face_names = socket.recv_pyobj()
        if 'person' in label:
            state[idn].value=1
        else:
            state[idn].value=0

def controllisten(quitter):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(controlleraddress)
    socket.setsockopt(zmq.SUBSCRIBE, b'q')
    while True:
        topic = socket.recv_string()
        com = socket.recv_pyobj()
        quitter.put(com)


class viewer(QLabel):
    def __init__(self, idn, parent=None):
        super(viewer, self).__init__(parent)
        self.setScaledContents(True)
        self.setMinimumSize(1,1)

        self.idn = idn
        self.tim = QTimer()
        self.tim.setInterval(50)
        self.tim.timeout.connect(self.beat)
        self.tim.start()
        self.skip = 0

    def beat(self):
        global loops
        if len(loops[self.idn].loop) > 0:
            im = loops[self.idn].step()
            self.display(im)

    def display(self,im):
        self.skip+=1
        if self.skip==2:
            self.skip=0
            return 
        nim = np.flip(im,2).copy()
        qimage = QImage(nim, nim.shape[1], nim.shape[0],QImage.Format_RGB888)
        pixmap = QPixmap(qimage)
        self.setPixmap(pixmap)

class mainwin(QMainWindow):
    def __init__(self, parent=None):
        super(mainwin, self).__init__(parent)

        self.setWindowTitle('Looper')
        frame = QFrame()
        self.setCentralWidget(frame)
        layout = QGridLayout()
        frame.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.resize(600,400)

        self.views = []
        idn=0
        for i in range(4):
            vw = viewer(idn)
            self.views.append(vw)
            layout.addWidget(vw,int(idn/2),idn%2)
            idn+=1

        self.quitter=mp.Queue()
        self.tim = QTimer()
        self.tim.setInterval(200)
        self.tim.timeout.connect(self.beat)
        self.tim.start()

    def beat(self):
        com=0
        try:
            com = self.quitter.get(False)
        except:
            pass
        if com==1: exit()

imageq = mp.Queue()
dataq = mp.Queue()
powerq = mp.Queue()
quitter = mp.Queue()
state = []
loops = []


for i in range(4):
    n = mp.Value('i',1)
    state.append(n)
    loops.append(looper())

if __name__=='__main__':
    t1 = threading.Thread(target=listen,args=(state,loops),daemon=True)
    t1.start()
    t2 = threading.Thread(target=datalisten,args=(state,),daemon=True)
    t2.start()
    t3 = threading.Thread(target=controllisten,args=(quitter,),daemon=True)
    t3.start()

    app = QApplication(sys.argv)
    form = mainwin()
    form.show()

    form.quitter = quitter

    # form.showFullScreen()
    form.showMaximized()
    form.raise_()
    app.exec_()
