import os
import time
import threading
import cv2
from PIL import Image
from brain import JarvisBrain

class CameraStreamer:
    """Continuous background frame grabber for 30 FPS live streaming and 0ms capture."""

    def __init__(self, camera_index=1):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        # Configure for 720p / 1080p high-speed capture
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.current_frame = None
        self.is_running = False
        self.lock = threading.Lock()

        if self.cap.isOpened():
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            print(f"[VISION ENGINE] Live 30 FPS optical streamer active on index {camera_index}")
        else:
            print(f"[ERROR] Could not open camera on index {camera_index}")

    def _capture_loop(self):
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self.lock:
                    self.current_frame = frame
            else:
                time.sleep(0.01)

    def get_latest_frame(self):
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_jpeg_bytes(self):
        frame = self.get_latest_frame()
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                return buffer.tobytes()
        return None

    def release(self):
        self.is_running = False
        if self.cap.isOpened():
            self.cap.release()

class JarvisVision:
    """High-Speed Multimodal Vision Controller."""

    def __init__(self, camera_index=1):
        self.brain = JarvisBrain()
        self.streamer = CameraStreamer(camera_index=camera_index)

    def snap_frame(self, save_path=None) -> str:
        """Grabs the active in-memory frame in ~5ms."""
        if not save_path:
            save_path = os.path.expanduser("~\\jarvis_eye.jpg")

        frame = self.streamer.get_latest_frame()
        if frame is not None:
            cv2.imwrite(save_path, frame)
            return save_path
        return None

    def see_and_reason(self, prompt="Describe what you observe through the live feed in 1-2 concise sentences.") -> dict:
        t0 = time.time()
        frame_path = self.snap_frame()
        t_capture = time.time() - t0

        if not frame_path:
            return {
                "text": "Live optical feed currently unavailable, Sir.",
                "latency": round(t_capture, 2)
            }

        result = self.brain.see(frame_path, prompt)
        total_time = round(t_capture + result["latency"], 2)
        return {
            "text": result["text"],
            "latency": total_time,
            "frame_path": frame_path
        }
