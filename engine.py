import cv2
import cvlib
from cvlib.object_detection import draw_bbox
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


def recvthings(qin,done):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b'p')
    current={}
    while True:
        topic = socket.recv_string()
        idn,frame,mvmt = socket.recv_pyobj()
        # frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
        while True:
            try:
                f = done.get(False)
                del current[f]
            except:
                break

        if not idn in current:
            qin.put((idn,frame,mvmt))
            current[idn]=1


def findthings(qin,done,qoo,imo):
    while True:
        idn, frame, mvmt = qin.get(True)
        # frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
        if mvmt:
            bbox, label, conf = cvlib.detect_common_objects(frame, confidence=0.85, enable_gpu=True)
            # bbox, label, conf = cvlib.detect_common_objects(frame, confidence=0.5, enable_gpu=False)
            # bbox, label, conf = cvlib.detect_common_objects(frame, confidence=0.5, model='yolov3-tiny')
        else:
            bbox = []
            label = []
            conf = []

        face_names = []
        done.put(idn)
        qoo.put((idn,bbox,label,face_names))

        frame = draw_bbox(frame, bbox, label, conf)
        ret_code, cframe = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        imo.put((idn,cframe,mvmt))


def sendthings(qoo):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5556")
    while True:
        idn,bbox,label,face_names = qoo.get()
        socket.send_string('d', zmq.SNDMORE)
        socket.send_pyobj((idn,bbox,label,face_names))

def sendvideo(imo):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5557")
    while True:
        idn,frame,mvmt = imo.get()
        socket.send_string('p', zmq.SNDMORE)
        socket.send_pyobj((idn,frame,mvmt))

qin = mp.Queue()
done = mp.Queue()
qoo = mp.Queue()
imo = mp.Queue()

rt = mp.Process(target=recvthings,args=(qin,done))
rt.start()

vt = mp.Process(target=sendvideo,args=(imo,))
vt.start()

pro = []
for i in range(1):
    ft = mp.Process(target=findthings,args=(qin,done,qoo,imo))
    ft.start()
    pro.append(ft)

sendthings(qoo)

print('hello there')
