from flask import Flask, render_template, Response
import cv2
from line_following import get_frames_for_server

app = Flask(__name__)

camera = cv2.VideoCapture(0)

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(get_frames_for_server(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)