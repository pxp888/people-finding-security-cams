import threading
import time
import os
import sys
import multiprocessing as mp
import zmq
import playsound

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

dataserver = "tcp://localhost:5556"
controlleraddress = "tcp://localhost:5558"

fil = open(filpath,'r')
sor = fil.read().split('\n')
fil.close()
for i in sor:
    n = i.split(': ')
    if n[0]=='dataserver':
        dataserver=n[1]
    if n[0]=='controller':
        controlleraddress = n[1]

#-------------------------------------SETUP COMPLETE

state = mp.Value('i',0)

def datalisten(state):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(dataserver)
    socket.setsockopt(zmq.SUBSCRIBE, b'd')
    while True:
        topic = socket.recv_string()
        idn,bbox,label,face_names = socket.recv_pyobj()
        if 'person' in label:
            if state.value==1:
                state.value=2

def controllisten(state):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(controlleraddress)
    socket.setsockopt(zmq.SUBSCRIBE, b'a')
    while True:
        topic = socket.recv_string()
        com = socket.recv_pyobj()
        state.value=com
        print('command',com)

def mainalarm(state):
    while True:
        if state.value==2:
            print('ALARM GOING OFF')
            os.system('aplay -q sounds/m1.wav')
        else:
            time.sleep(1)


if __name__=='__main__':
    datathread = threading.Thread(target=datalisten,args=(state,),daemon=True)
    datathread.start()

    conthread = threading.Thread(target=controllisten,args=(state,),daemon=True)
    conthread.start()

    mainalarm(state)
