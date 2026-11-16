import os
import time
import threading
import cv2
from PIL import Image
from brain import JarvisBrain

class CameraStreamer:
    """Non-blocking background camera streamer with fallback placeholder."""

    def __init__(self, camera_index=1):
        self.camera_index = camera_index
        self.current_frame = None
        self.is_running = True
        self.lock = threading.Lock()
        
        # Start capture loop in daemon thread
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def _capture_worker(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # If camera index 1 fails, fallback to index 0 (Integrated Camera)
        if not cap.isOpened():
            print(f"[WARN] Camera {self.camera_index} unavailable. Falling back to index 0...")
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        while self.is_running:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.current_frame = frame
                else:
                    time.sleep(0.02)
            else:
                time.sleep(0.1)

    def get_latest_frame(self):
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_jpeg_bytes(self):
        frame = self.get_latest_frame()
        if frame is not None:
            ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                return buf.tobytes()
        return None

class JarvisVision:
    def __init__(self, camera_index=1):
        self.brain = JarvisBrain()
        self.streamer = CameraStreamer(camera_index=camera_index)

    def snap_frame(self, save_path=None) -> str:
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
            return {"text": "Live camera feed is locked or unavailable, Sir.", "latency": round(t_capture, 2)}

        result = self.brain.see(frame_path, prompt)
        return {
            "text": result["text"],
            "latency": round(t_capture + result["latency"], 2),
            "frame_path": frame_path
        }
