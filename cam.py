# from PyQt5.QtCore import *
# from PyQt5.QtWidgets import *
# from PyQt5.QtGui import *
# from PyQt5.QtNetwork import *

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
import zlib
import socket
import time
import msgpack
import zmq

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
    if n[0]=='cam':
        sources.append(n[1])

#-------------------------------------SETUP COMPLETE





def shrink(frame,targetsize=800):
    siz = np.max(frame.shape)
    nim = cv2.resize(frame, (0, 0), fx=targetsize/siz, fy=targetsize/siz)
    return nim

def getimage(source, idn, qin, control):
    first=True
    video_capture = cv2.VideoCapture(source)
    if source==0:
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    cut = time.time()
    while True:
        try:
            ret,frame = video_capture.read()
            frame = shrink(frame)
            # ret_code, cframe = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        except:
            video_capture = cv2.VideoCapture(source)
            continue
        if not ret:
            video_capture = cv2.VideoCapture(source)
            continue

        small = cv2.resize(frame, (40, 30))
        small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if first:
            first=False
            mvmt = True
        else:
            test = cv2.absdiff(small,prev)
            ret, test1 = cv2.threshold(test,25,255,cv2.THRESH_BINARY)
            movement = np.sum(test1==255)
            tim = time.time()
            if movement > 1:
                cut = tim + 5
            if tim < cut:
                mvmt = True
            else:
                mvmt = False

        prev = small
        if control.value==1: mvmt = False
        if not control.value==0:
            qin.put((idn, frame, mvmt))

def broadcast(qin):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    while True:
        idn, frame, mvmt = qin.get()
        socket.send_string('p', zmq.SNDMORE)
        socket.send_pyobj((idn,frame,mvmt))


def listen(control):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(controlleraddress)
    socket.setsockopt(zmq.SUBSCRIBE, b'c')
    while True:
        topic = socket.recv_string()
        com = socket.recv_pyobj()
        control.value = com
        print('recv',com)


control = mp.Value('i',2)
pin = mp.Queue()
pro = []
idn = 0
for s in sources:
    n = threading.Thread(target=getimage,args=(s,idn,pin,control))
    n.start()
    pro.append(n)
    idn+=1

cont = threading.Thread(target=listen,args=(control,))
cont.start()


broadcast(pin)
