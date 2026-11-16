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
            "

@'
import os
import threading
from flask import Flask, render_template, jsonify, request, Response
from brain import JarvisBrain
from voice import JarvisVoice
from controller import WindowsController
from vision import JarvisVision

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Shared Subsystems
brain = JarvisBrain()
voice = JarvisVoice()
ctrl = WindowsController()
vision = JarvisVision(camera_index=1)

def speak_async(text):
    """Speaks aloud in a background thread to prevent blocking the UI."""
    threading.Thread(target=voice.speak, args=(text,), daemon=True).start()

def generate_video_stream():
    """Generates continuous MJPEG frames for live HUD streaming."""
    while True:
        frame_bytes = vision.streamer.get_jpeg_bytes()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.033)  # ~30 FPS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    """Live 30 FPS Camera Feed."""
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/status", methods=["GET"])
def get_status():
    status = ctrl.get_system_status()
    return jsonify(status)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    res = brain.think(prompt)
    speak_async(res["text"])
    return jsonify(res)

@app.route("/api/vision/snap", methods=["POST"])
def vision_snap():
    """Instantaneous optical reasoning over active memory buffer."""
    data = request.json or {}
    custom_prompt = data.get("prompt", "Analyze what you see in front of the lens in 1-2 concise sentences.")
    res = vision.see_and_reason(custom_prompt)
    speak_async(res["text"])
    return jsonify(res)

@app.route("/api/voice/listen", methods=["POST"])
def voice_listen():
    audio_bytes = voice.record_mic(duration=4)
    res = brain.listen(audio_bytes)
    speak_async(res["text"])
    return jsonify(res)

@app.route("/api/action", methods=["POST"])
def execute_action():
    data = request.json or {}
    action_type = data.get("action")
    target = data.get("target")

    if action_type == "volume":
        msg = ctrl.set_system_volume(int(target))
    elif action_type == "app":
        msg = ctrl.open_application(str(target))
    elif action_type == "screenshot":
        p = ctrl.capture_screenshot()
        msg = f"Screenshot saved to {p}"
    else:
        msg = "Unknown action requested."

    return jsonify({"result": msg})

if __name__ == "__main__":
    print("\n=======================================================")
    print(" >>> JARVIS ULTRA-PERFORMANCE HUD INITIALIZED <<<")
    print(" >>> Live 30 FPS Stream Active: http://127.0.0.1:5000 <<<")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
