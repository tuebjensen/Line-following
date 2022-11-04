from flask import Flask, render_template, Response

class VideoStreaming:

    def __init__(self):
        self._is_running = False
        self._frame_encoded = None

    def set_frame_encoded(self, frame_encoded):
        self._frame_encoded = frame_encoded

    def start_running(self):
        if self._is_running:
            return
        self._is_running = True

        app = Flask(__name__)

        def show_image():
            while True:  
                yield (
                    b'--frame\r\n'
                    + b'Content-Type: image/jpeg\r\n\r\n' 
                    + (self._frame_encoded if self._frame_encoded is not None else b'') 
                    + b'\r\n'
                )            

        # Setup test server
        @app.route('/video_feed')
        def video_feed():
            #Video streaming route. Put this in the src attribute of an img tag
            return Response(show_image(), mimetype='multipart/x-mixed-replace; boundary=frame')

        @app.route('/')
        def index():
            """Video streaming home page."""
            return render_template('index.html')
        
        # Run test server
        app.run(host='0.0.0.0', debug=True, threaded=True )
            

