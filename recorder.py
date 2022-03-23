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


def vidname(idn, t=0):
        if t==0: t = time.time()
        a = datetime.datetime.fromtimestamp(t)
        b = a.astimezone(pytz.timezone("Asia/Manila"))
        n = b.strftime("-%y%m%d %H%M%S")
        return '/media/'+str(idn) + str(n)


def listen(pins):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(camserver)
    socket.setsockopt(zmq.SUBSCRIBE, b'p')
    while True:
        topic = socket.recv_string()
        idn,frame,mvmt = socket.recv_pyobj()
        frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
        pins[idn].put(frame)


def datalisten(qins):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(dataserver)
    socket.setsockopt(zmq.SUBSCRIBE, b'd')
    while True:
        topic = socket.recv_string()
        idn,bbox,label,face_names = socket.recv_pyobj()
        qins[idn].put(label)


def record(idn,pin,qin):
    frame = pin.get(True)
    vsize = (frame.shape[1],frame.shape[0])

    rec = False
    tim = time.time()
    cut = tim+3
    while True:
        label = qin.get(True)
        tim = time.time()
        if 'person' in label:
            cut = tim + 60
            if not rec:
                rec = True
                fourcc = cv2.VideoWriter_fourcc(*"H264")
                vw = cv2.VideoWriter(vidname(idn) + '.avi', fourcc, 12, vsize )

        if rec:
            while True:
                try:
                    frame = pin.get(False)
                    vw.write(frame)
                except:
                    break
        else:
            while pin.qsize() > 36:
                pin.get(True)

        if tim > cut:
            if rec:
                rec = False
                vw.release()

pins = []
qins = []
# pro = []

for i in range(4):
    pin = mp.Queue(60)
    qin = mp.Queue()
    pins.append(pin)
    qins.append(qin)

    n = threading.Thread(target=record,args=(i,pin,qin))
    n.start()
    # pro.append(n)

lt = threading.Thread(target=listen,args=(pins,))
lt.start()

datalisten(qins)
