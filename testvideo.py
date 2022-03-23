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

cap = cv2.VideoCapture(sys.argv[1])
ret,frame = cap.read()

vsize = (frame.shape[1],frame.shape[0])
fourcc = cv2.VideoWriter_fourcc(*"H264")
vw = cv2.VideoWriter('/home/output.avi', fourcc, 12, vsize )

skip = 0
count = 0
while True:
    ret, frame = cap.read()
    if not ret: break
    skip+=1
    if skip>1:
        skip=0
        bbox, label, conf = cvlib.detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        frame = draw_bbox(frame, bbox, label, conf)
        vw.write(frame)

        count+=1
        if 'person' in label:
            print(label, conf, float(count)/12)

        # cv2.imshow(sys.argv[1],frame)
        # cv2.waitKey(1)

cap.release()
vw.release()
cv2.destroyAllWindows()
print('-----------------------------')



#sudo docker run --rm -ti --gpus all --name "bob" -v /home/pxp/Desktop/engine/:/home/ --net host  723fc40c2314 bash
