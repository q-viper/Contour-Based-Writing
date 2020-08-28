from flask import Flask, render_template, Response
import cv2
import numpy as np
import matplotlib.pyplot as plt
from main import *
import time


err_img=cv2.imread("static\error_frame.png")
_, err_img_byte = cv2.imencode(".jpg", err_img)
err_img_byte = err_img_byte.tobytes()
draw=None



class GestureWeb:
    def __init__(self, port=5005, debug=True):
        self.detected_text = "Nothing"
        self.camera= ContourWriting()
        
    def frame_gen(self, camera, kind="frame"):        
        while True:    
            frame = camera.main()
            if frame is None:
                frame = (None, None)
            if frame[0] is None:
                frame = err_img_byte
            elif frame[1] is None:
                draw = err_img_byte
            else:
                frame, draw, gw.detected_text = frame
                #print("in framegen", detected_text)
            frame = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'+bytearray(frame)+b'\r\n')
            draw = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'+bytearray(draw)+b'\r\n')
            if kind =="frame":
                yield frame
            if kind =="draw":
                yield draw
            if kind=="text":
                yield detected_text

    
    
  
app = Flask(__name__)

@app.before_first_request
def before_first_request_func():
    global gw 
    gw = GestureWeb()
    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_canvas')
def get_canvas():
    fresp = gw.frame_gen(gw.camera, "draw")    
    return Response(fresp, mimetype='multipart/x-mixed-replace; boundary=frame')

    
@app.route('/video_feed')
def video_feed():
    fresp = gw.frame_gen(gw.camera, kind="frame")
    return Response(fresp, mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route('/detection.html', methods=['GET', 'POST'])
def detect():
    return render_template("detection.html", detected_text=gw.detected_text)
    
@app.teardown_request
def teardown_request_func(error=None):
    global gw
    gw = GestureWeb()   
    return "ok"



if __name__=='__main__':    
    app.run(debug=True)
    
    