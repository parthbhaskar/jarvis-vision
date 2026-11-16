import os
import time
import threading
import cv2
import numpy as np
from PIL import Image
from brain import JarvisBrain

class CameraStreamer:
    """Threaded camera grabber supporting GoPro and Laptop Webcam with HUD graphic."""

    def __init__(self, camera_index=1):
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
            print(f"[VISION] Switched camera to index {new_index}")

    def _open_camera(self):
        # Index 1 (GoPro) prefers 1080p; Index 0 (Laptop) uses default
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if self.camera_index == 1:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        return cap

    def _generate_standby_frame(self):
        """Generates a cinematic HUD graphic when the camera sensor is warming up."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Deep navy background
        img[:] = (17, 8, 5)
        # Grid lines
        cv2.rectangle(img, (20, 20), (620, 460), (255, 240, 0), 1)
        cv2.putText(img, "JARVIS OPTICAL SENSOR // STANDBY", (120, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 240, 0), 2)
        cv2.putText(img, f"Active Index: {self.camera_index} (Click 'SWITCH CAMERA' to toggle)", (100, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        cv2.putText(img, f"System Clock: {time.strftime('%H:%M:%S')}", (220, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
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
                    # If frame is pure black, feed the standby HUD graphic
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
