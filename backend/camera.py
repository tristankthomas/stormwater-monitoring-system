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

# shared mutable thresholds for the opencv analysis, adjustable at runtime via /api/camera/thresholds
vision_thresholds = {
    "clear_brightness": 100.0,   # mean brightness above this = clear water
    "turbid_brightness": 60.0,   # mean brightness below this = high turbidity
    "debris_min_area": 500.0,    # minimum contour area (px) to count as debris
}
DEFAULT_VISION_THRESHOLDS = dict(vision_thresholds)


class CameraProcessor:
    def __init__(self):
        self.frame = None           # latest raw frame as jpeg bytes
        self.picam = None
        self.camera_ready = False   # true only if a camera was found and started
        self.analysis = {
            "turbidity_class": "unknown",
            "clarity_index": None,
            "debris_count": 0,
            "brightness": None,
            "available": False
        }
        self.lock = threading.Lock()
        self.running = False

        if CAMERA_AVAILABLE:
            self._init_camera()
            self.analysis["available"] = self.camera_ready

    def _init_camera(self):
        # initialise picamera2 and configure for video capture
        # if no camera is attached, carry on without one so the rest of the app still runs
        try:
            self.picam = Picamera2()
            config = self.picam.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.picam.configure(config)
            self.picam.start()
            time.sleep(1)  # allow camera to warm up before first capture
            self.camera_ready = True
        except Exception as e:
            print(f"camera not available: {e}")
            self.picam = None
            self.camera_ready = False

    def start(self):
        if not self.camera_ready:
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
        clear = vision_thresholds["clear_brightness"]
        turbid = vision_thresholds["turbid_brightness"]
        debris_min_area = vision_thresholds["debris_min_area"]

        # convert to greyscale for brightness and contour analysis
        grey = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        brightness = float(np.mean(grey))

        # classify turbidity based on average pixel brightness
        if brightness > clear:
            turbidity_class = "clear"
        elif brightness > turbid:
            turbidity_class = "moderate"
        else:
            turbidity_class = "high"

        # continuous clarity index: 0 at or above the clear threshold, 1 at the turbid threshold
        # (the "high" class boundary), capped at 2 for very dark frames
        span = max(clear - turbid, 1.0)
        clarity_index = max(0.0, min((clear - brightness) / span, 2.0))

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
        debris_count = sum(1 for c in contours if cv2.contourArea(c) > debris_min_area)

        return {
            "turbidity_class": turbidity_class,
            "clarity_index": round(clarity_index, 3),
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
        if self.picam is not None:
            self.picam.stop()


# single shared camera instance used across the app
camera = CameraProcessor()