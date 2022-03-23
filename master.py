from pynput.mouse import Button, Controller
from pynput import keyboard
import socket
import threading
import time
import os
import sys
import multiprocessing as mp
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

def shout(conq):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5558")
    while True:
        k, val = conq.get()
        socket.send_string( k, zmq.SNDMORE )
        socket.send_pyobj(val)

def datalisten(state, alarmq, powerq):
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
                alarmq.put(1)
                powerq.put(1)

def poweron(powerq):
    while True:
        n = powerq.get(True)
        if n==1:
            os.system("echo 'as' | cec-client -s -d 1")
            print('power ON -------------------')
            time.sleep(1)
        if n==0:
            os.system("echo 'standby 0.0.0.0' | cec-client -s -d 1")
            print('power OFF -------------------')
            time.sleep(1)

def alarm(alarmq):
    while True:
        n = alarmq.get(True)
        os.system('python looper.py')


state = mp.Value('i',0)
alarmq = mp.Queue()
powerq = mp.Queue()
conq = mp.Queue()
# off, view, record, tv, alarm


# WHAT THIS SHOULD DO
# camera modes - off, view only, record  -- 3
# alarm modes - on, off -- 2
# viewer modes - show loops, TV off -- 2

def on_press(key):
    # print(key)
    # if key == keyboard.Key.f1:
    if hasattr(key,'char'):
        if key.char=='0':
            print('z 0')
            conq.put(('c',0))
            conq.put(('a',0))
            conq.put(('q',1))
            state.value=0

    if hasattr(key,'char'):
        if key.char=='1':
            conq.put(('c',1))
            conq.put(('a',0))
            conq.put(('q',1))
            state.value=0

    if hasattr(key,'char'):
        if key.char=='2':
            conq.put(('c',2))
            conq.put(('a',0))
            conq.put(('q',1))
            state.value=0

    if hasattr(key,'char'):
        if key.char=='3':
            conq.put(('c',2))
            conq.put(('a',0))
            conq.put(('q',1))
            state.value=1

    if hasattr(key,'char'):
        if key.char=='4':
            conq.put(('c',2))
            conq.put(('a',1))
            conq.put(('q',1))
            state.value=1

    if hasattr(key,'char'):
        if key.char=='7':
            alarmq.put(1)
            powerq.put(1)
            state.value=2




def on_release(key):
    pass



if __name__=='__main__':
    t1 = threading.Thread(target=shout,args=(conq,),daemon=True)
    t1.start()
    t2 = threading.Thread(target=datalisten,args=(state, alarmq, powerq),daemon=True)
    t2.start()
    t3 = threading.Thread(target=poweron,args=(powerq,),daemon=True)
    t3.start()
    t4 = threading.Thread(target=alarm,args=(alarmq,),daemon=True)
    t4.start()

    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
