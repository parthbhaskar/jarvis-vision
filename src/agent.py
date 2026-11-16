import os
import time
from brain import JarvisBrain
from voice import JarvisVoice
from controller import WindowsController
from vision import JarvisVision
from google.genai import types

# Initialize subsystems
brain = JarvisBrain()
voice = JarvisVoice()
ctrl = WindowsController()
vision = JarvisVision(camera_index=1)

# Approved Tool Declarations for Gemini
tools_definition = [
    {
        "name": "get_system_telemetry",
        "description": "Reads current laptop battery percentage, charging state, free SSD storage, RAM usage, and time."
    },
    {
        "name": "set_master_volume",
        "description": "Adjusts Windows master speaker volume from 0 to 100 percent.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"level": {"type": "INTEGER", "description": "Volume level 0 to 100"}},
            "required": ["level"]
        }
    },
    {
        "name": "open_application",
        "description": "Launches approved applications like Calculator, Notepad, Edge, Chrome, Spotify.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"app_name": {"type": "STRING", "description": "Application name"}},
            "required": ["app_name"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Captures a silent screenshot of the primary Windows display."
    },
    {
        "name": "look_through_camera",
        "description": "Snaps a live frame from the GoPro camera to observe the physical room or desk surroundings."
    }
]

def execute_action(tool_call) -> str:
    name = tool_call.name
    args = tool_call.args or {}
    print(f"\n[ACTION EXECUTED]: {name}({args})")

    if name == "get_system_telemetry":
        s = ctrl.get_system_status()
        return f"Battery: {s['battery']}, Free SSD: {s['free_storage_gb']}, RAM: {s['ram_used_percent']}, Time: {s['local_time']}"
    elif name == "set_master_volume":
        return ctrl.set_system_volume(args.get("level", 50))
    elif name == "open_application":
        return ctrl.open_application(args.get("app_name", ""))
    elif name == "take_screenshot":
        p = ctrl.capture_screenshot()
        return f"Desktop screenshot captured and saved to {p}."
    elif name == "look_through_camera":
        res = vision.see_and_reason("Describe what you observe in 1 concise sentence.")
        return res["text"]
    return "Action completed successfully."

def run_agent_turn():
    # 1. Record User Voice
    audio_bytes = voice.record_mic(duration=4)

    system_instruction = (
        "You are JARVIS, an advanced personal AI systems assistant on Windows 11. "
        "Listen to the user's spoken command. "
        "If they request system stats, volume adjustment, opening an app, taking a screenshot, "
        "or looking through the camera, call the matching tool. "
        "Always address the user politely as Sir in one concise, professional sentence."
    )

    t0 = time.time()
    # 2. Let Gemini reason over raw audio and choose actions
    response = brain.client.models.generate_content(
        model=brain.model_name,
        contents=[
            system_instruction,
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        ],
        config=types.GenerateContentConfig(
            tools=[{"function_declarations": tools_definition}]
        )
    )

    # 3. Handle Tool Calling or Direct Response
    if response.function_calls:
        tool_call = response.function_calls[0]
        action_result = execute_action(tool_call)
        
        # Follow-up with synthesized speech response
        followup = brain.client.models.generate_content(
            model=brain.model_name,
            contents=[
                system_instruction,
                f"Action execution result: {action_result}. Report this to the user in one crisp sentence."
            ]
        )
        latency = round(time.time() - t0, 2)
        print(f"[ROUNDTRIP TIME]: {latency}s")
        voice.speak(followup.text.strip())
    else:
        latency = round(time.time() - t0, 2)
        print(f"[ROUNDTRIP TIME]: {latency}s")
        voice.speak(response.text.strip())

if __name__ == "__main__":
    voice.speak("System integration complete on Windows 11. Standing by for your command, Sir.")
    input("\nPress [ENTER], then speak: 'JARVIS, check my battery level and set volume to 50 percent' ...")
    run_agent_turn()
