import os
import time
import threading
from flask import Flask, render_template, jsonify, request, Response
from brain import JarvisBrain
from voice import JarvisVoice
from controller import WindowsController
from vision import JarvisVision
from google.genai import types

app = Flask(__name__, template_folder="../templates", static_folder="../static")

brain = JarvisBrain()
voice = JarvisVoice()
ctrl = WindowsController()
# Default to index 2 (GoPro) or 0 (Laptop)
vision = JarvisVision(camera_index=2)

# Persistent Multi-Turn Conversation History
conversation_history = []

tools_definition = [
    {"name": "get_system_telemetry", "description": "Reads battery, free storage, RAM, and time."},
    {"name": "set_master_volume", "description": "Adjusts volume 0-100", "parameters": {"type": "OBJECT", "properties": {"level": {"type": "INTEGER"}}, "required": ["level"]}},
    {"name": "open_application", "description": "Launches apps like calc, notepad", "parameters": {"type": "OBJECT", "properties": {"app_name": {"type": "STRING"}}, "required": ["app_name"]}},
    {"name": "take_screenshot", "description": "Takes silent desktop screenshot."},
    {"name": "look_through_camera", "description": "Observes and analyzes the live camera feed."}
]

def speak_async(text):
    threading.Thread(target=voice.speak, args=(text,), daemon=True).start()

def generate_video_stream():
    while True:
        frame_bytes = vision.streamer.get_jpeg_bytes()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.033)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/camera/switch", methods=["POST"])
def switch_camera():
    data = request.json or {}
    idx = int(data.get("index", 0))
    vision.streamer.switch_camera(idx)
    return jsonify({"status": "success", "active_index": idx})

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(ctrl.get_system_status())

@app.route("/api/chat", methods=["POST"])
def chat():
    """Agentic chat route with persistent multi-turn memory."""
    global conversation_history
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    system_instruction = (
        "You are JARVIS on Windows 11. Maintain continuous conversational memory with the user. "
        "If the user asks about the room, objects, or camera, call look_through_camera. "
        "If they ask for system info, volume, screenshot, or apps, call the matching tool. "
        "Address user politely as Sir in one concise, intelligent sentence."
    )

    t0 = time.time()
    try:
        # Append user turn to persistent memory
        conversation_history.append(f"USER: {prompt}")
        recent_context = "\n".join(conversation_history[-10:])

        response = brain.client.models.generate_content(
            model=brain.model_name,
            contents=[system_instruction, f"Conversation context:\n{recent_context}"],
            config=types.GenerateContentConfig(tools=[{"function_declarations": tools_definition}])
        )

        if response.function_calls:
            call = response.function_calls[0]
            name = call.name
            args = call.args or {}
            
            if name == "look_through_camera":
                result = vision.see_and_reason("Describe what you observe through the live feed in 1-2 concise sentences.")["text"]
            elif name == "get_system_telemetry":
                s = ctrl.get_system_status()
                result = f"Battery: {s['battery']}, Free SSD: {s['free_storage_gb']}, RAM: {s['ram_used_percent']}"
            elif name == "set_master_volume":
                result = ctrl.set_system_volume(args.get("level", 50))
            elif name == "open_application":
                result = ctrl.open_application(args.get("app_name", ""))
            elif name == "take_screenshot":
                result = f"Screenshot captured: {ctrl.capture_screenshot()}"
            else:
                result = "Action completed."

            followup = brain.client.models.generate_content(
                model=brain.model_name,
                contents=[system_instruction, f"Tool execution result: {result}. Formulate final response to user as Sir in 1 concise sentence."]
            )
            reply = followup.text.strip()
        else:
            reply = response.text.strip()

        # Append assistant turn to persistent memory
        conversation_history.append(f"JARVIS: {reply}")
        latency = round(time.time() - t0, 2)
        speak_async(reply)
        return jsonify({"text": reply, "latency": latency})

    except Exception as e:
        print(f"[ERROR in chat]: {e}")
        return jsonify({"text": "I encountered a minor cognitive delay, Sir.", "latency": 0.0})

@app.route("/api/vision/snap", methods=["POST"])
def vision_snap():
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
    act = data.get("action")
    tgt = data.get("target")

    if act == "volume":
        msg = ctrl.set_system_volume(int(tgt))
    elif act == "app":
        msg = ctrl.open_application(str(tgt))
    elif act == "screenshot":
        msg = f"Screenshot saved to {ctrl.capture_screenshot()}"
    else:
        msg = "Unknown action."

    return jsonify({"result": msg})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
