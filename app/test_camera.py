from flask import Flask, render_template, Response
import cv2 as cv

app = Flask(__name__)

cap = cv.VideoCapture(0)
def show_image():

    while cap.isOpened():
        ret, original_frame = cap.read()
        original_frame = original_frame[:, 30:]
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
    ret, buffer = cv.imencode('.jpg', frame)
    frame = buffer.tobytes()
    yield (b'--frame\r\n'
    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
    cap.release()

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(show_image(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)