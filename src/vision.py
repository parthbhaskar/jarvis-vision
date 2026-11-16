import os
import time
import threading
import cv2
import numpy as np
from PIL import Image
from brain import JarvisBrain

class CameraStreamer:
    """1080p Full HD continuous frame streamer with multi-camera scanning."""

    def __init__(self, camera_index=2):
        self.camera_index = camera_index
        self.current_frame = None
        self.is_running = True
        self.cap = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def switch_camera(self, new_index: int):
        with self.lock:
            self.camera_index = new_index
            if self.cap and self.cap.isOpened():
                self.cap.release()
            self.cap = None
            print(f"[VISION] Active camera switched to index {new_index}")

    def _open_camera(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        # Enforce 1080p Full HD
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        return cap

    def _generate_standby_frame(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        img[:] = (17, 8, 5)
        cv2.rectangle(img, (30, 30), (1250, 690), (255, 240, 0), 2)
        cv2.putText(img, "JARVIS 1080p OPTICAL FEED // STANDBY", (320, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 240, 0), 2)
        cv2.putText(img, f"Active Camera Index: {self.camera_index}", (440, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)
        cv2.putText(img, "Select camera from dropdown above if feed is dark", (360, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 1)
        return img

    def _capture_worker(self):
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = self._open_camera()
                time.sleep(0.5)

            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.mean() > 5:
                    with self.lock:
                        self.current_frame = frame
                else:
                    with self.lock:
                        self.current_frame = self._generate_standby_frame()
                    time.sleep(0.04)
            else:
                with self.lock:
                    self.current_frame = self._generate_standby_frame()
                time.sleep(0.5)

    def get_latest_frame(self):
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return self._generate_standby_frame()

    def get_jpeg_bytes(self):
        frame = self.get_latest_frame()
        # Encode at high quality (85%)
        ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            return buf.tobytes()
        return None

class JarvisVision:
    def __init__(self, camera_index=2):
        self.brain = JarvisBrain()
        self.streamer = CameraStreamer(camera_index=camera_index)

    def snap_frame(self, save_path=None) -> str:
        if not save_path:
            save_path = os.path.expanduser("~\\jarvis_eye.jpg")
        frame = self.streamer.get_latest_frame()
        cv2.imwrite(save_path, frame)
        return save_path

    def see_and_reason(self, prompt="Describe what you observe through the live feed in 1-2 concise sentences.") -> dict:
        t0 = time.time()
        frame_path = self.snap_frame()
        result = self.brain.see(frame_path, prompt)
        return {
            "text": result["text"],
            "latency": round(time.time() - t0, 2),
            "frame_path": frame_path
        }
