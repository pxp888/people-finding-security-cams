FROM datamachines/cudnn_tensorflow_opencv:10.2_2.1.0_4.3.0-20200423

ADD cvlib/ /root/.cvlib/

RUN apt-get install -y --no-install-recommends libnvinfer6=6.0.1-1+cuda10.1 \
    libnvinfer-dev=6.0.1-1+cuda10.1 \
    libnvinfer-plugin6=6.0.1-1+cuda10.1 \
    python3-pyqt5

RUN pip3 install \
    face_recognition \
    cvlib \
    msgpack \
    pytz \
    imagezmq 
	
