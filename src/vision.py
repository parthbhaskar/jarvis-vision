import os
import time
import cv2
from PIL import Image
from brain import JarvisBrain

class JarvisVision:
    """Optimized Optical Vision Engine with Sensor Warmup Handling."""

    def __init__(self, camera_index=1):
        self.brain = JarvisBrain()
        self.camera_index = camera_index

    def snap_frame(self, save_path=None) -> str:
        """Captures a frame, waiting for actual optical sensor light."""
        if not save_path:
            save_path = os.path.expanduser("~\\jarvis_eye.jpg")

        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print(f"[ERROR] Could not open camera index {self.camera_index}")
            return None

        # Request 1080p
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        frame = None
        t_start = time.time()
        
        # Poll for up to 3.5 seconds until optical sensor provides illuminated pixels
        while time.time() - t_start < 3.5:
            ret, temp = cap.read()
            if ret and temp is not None:
                # Check average pixel brightness (mean > 15 means real image, not black boot buffer)
                if temp.mean() > 15:
                    frame = temp
                    break
                else:
                    frame = temp  # keep latest frame even if dim
            time.sleep(0.05)

        cap.release()

        if frame is not None:
            cv2.imwrite(save_path, frame)
            return save_path
        return None

    def see_and_reason(self, prompt="Describe what you observe in front of you in 1 concise, professional sentence.") -> dict:
        """Snaps a frame and asks Gemini to analyze it."""
        t0 = time.time()
        frame_path = self.snap_frame()
        t_capture = time.time() - t0

        if not frame_path:
            return {
                "text": "Vision capture failed: Unable to acquire camera feed, Sir.",
                "latency": round(t_capture, 2)
            }

        print(f"[VISION] Frame acquired in {t_capture:.2f}s. Sending to Gemini...")
        result = self.brain.see(frame_path, prompt)
        total_time = round(t_capture + result["latency"], 2)
        return {
            "text": result["text"],
            "latency": total_time,
            "frame_path": frame_path
        }

if __name__ == "__main__":
    print("\n--- RE-TESTING GOPRO VISION (OPTICAL SENSOR WAKEUP) ---")
    vision = JarvisVision(camera_index=1)
    res = vision.see_and_reason("What physical objects and environment do you observe right now?")
    print(f"\n[STATUS: SUCCESS] Total Roundtrip Latency: {res['latency']}s")
    print(f"[JARVIS VISUAL ANALYSIS]:\n\"{res['text']}\"\n")
    
    # Automatically open the photo so you can see it on your screen
    os.system(f"start {res['frame_path']}")
