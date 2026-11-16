import os
import shutil
import tempfile
from flask import Flask, render_template, jsonify, request, send_file
from brain import JarvisBrain
from voice import JarvisVoice
from controller import WindowsController
from vision import JarvisVision

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Subsystems
brain = JarvisBrain()
voice = JarvisVoice()
ctrl = WindowsController()
vision = JarvisVision(camera_index=1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns real-time laptop telemetry."""
    status = ctrl.get_system_status()
    return jsonify(status)

@app.route("/api/chat", methods=["POST"])
def chat():
    """Text-based inquiry with neural voice reply."""
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    res = brain.think(prompt)
    # Speak reply asynchronously or in background
    voice.speak(res["text"])
    return jsonify(res)

@app.route("/api/vision/snap", methods=["POST"])
def vision_snap():
    """Snaps a frame from GoPro and analyzes it with Gemini."""
    res = vision.see_and_reason("Describe what you observe through the camera in 2 concise sentences.")
    voice.speak(res["text"])
    return jsonify(res)

@app.route("/api/vision/latest_frame", methods=["GET"])
def latest_frame():
    """Serves the latest captured image."""
    img_path = os.path.expanduser("~\\jarvis_eye.jpg")
    if os.path.exists(img_path):
        return send_file(img_path, mimetype="image/jpeg")
    return jsonify({"error": "No frame captured yet"}), 404

@app.route("/api/voice/listen", methods=["POST"])
def voice_listen():
    """Listens to microphone, passes to Gemini, and executes action."""
    audio_bytes = voice.record_mic(duration=4)
    res = brain.listen(audio_bytes)
    voice.speak(res["text"])
    return jsonify(res)

@app.route("/api/action", methods=["POST"])
def execute_action():
    """Executes a system automation action."""
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
    print(" >>> JARVIS VISION WEB DASHBOARD INITIALIZED <<<")
    print(" >>> Open your browser: http://127.0.0.1:5000        <<<")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
