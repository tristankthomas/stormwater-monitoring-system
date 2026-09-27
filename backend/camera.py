import cv2
import numpy as np
import threading
import time

# picamera2 is only available on the pi, import conditionally
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# thresholds for opencv turbidity classification based on image brightness
TURBIDITY_BRIGHT_THRESHOLD = 100  # above this = clear water
TURBIDITY_DARK_THRESHOLD = 60     # below this = high turbidity

# minimum contour area to count as debris (filters out noise)
DEBRIS_MIN_AREA = 500


class CameraProcessor:
    def __init__(self):
        self.frame = None           # latest raw frame as jpeg bytes
        self.analysis = {
            "turbidity_class": "unknown",
            "debris_count": 0,
            "brightness": None,
            "available": CAMERA_AVAILABLE
        }
        self.lock = threading.Lock()
        self.running = False

        if CAMERA_AVAILABLE:
            self._init_camera()

    def _init_camera(self):
        # initialise picamera2 and configure for video capture
        self.picam = Picamera2()
        config = self.picam.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam.configure(config)
        self.picam.start()
        time.sleep(1)  # allow camera to warm up before first capture

    def start(self):
        if not CAMERA_AVAILABLE:
            return
        self.running = True
        # run capture loop in background thread so it doesn't block the api
        thread = threading.Thread(target=self._capture_loop, daemon=True)
        thread.start()

    def _capture_loop(self):
        while self.running:
            try:
                frame = self.picam.capture_array()
                analysis = self._analyse_frame(frame)

                # encode frame to jpeg for streaming
                _, jpeg = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

                with self.lock:
                    self.frame = jpeg.tobytes()
                    self.analysis = analysis

            except Exception as e:
                print(f"camera capture error: {e}")

            time.sleep(0.1)  # ~10fps, sufficient for water monitoring

    def _analyse_frame(self, frame: np.ndarray) -> dict:
        # convert to greyscale for brightness and contour analysis
        grey = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        brightness = float(np.mean(grey))

        # classify turbidity based on average pixel brightness
        if brightness > TURBIDITY_BRIGHT_THRESHOLD:
            turbidity_class = "clear"
        elif brightness > TURBIDITY_DARK_THRESHOLD:
            turbidity_class = "moderate"
        else:
            turbidity_class = "high"

        # detect debris using adaptive thresholding and contour detection
        blurred = cv2.GaussianBlur(grey, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # count only contours large enough to be real debris
        debris_count = sum(1 for c in contours if cv2.contourArea(c) > DEBRIS_MIN_AREA)

        return {
            "turbidity_class": turbidity_class,
            "debris_count": debris_count,
            "brightness": round(brightness, 2),
            "available": True
        }

    def get_frame(self) -> bytes | None:
        with self.lock:
            return self.frame

    def get_analysis(self) -> dict:
        with self.lock:
            return self.analysis.copy()

    def stop(self):
        self.running = False
        if CAMERA_AVAILABLE:
            self.picam.stop()


# single shared camera instance used across the app
camera = CameraProcessor()
