import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

class JarvisBrain:
    """Core Cognitive Engine powered by Google Gemini."""

    def __init__(self, model_name="gemini-3.5-flash-lite"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.system_instruction = (
            "You are JARVIS, an advanced, highly capable personal AI assistant. "
            "You communicate concisely, professionally, and address the user respectfully as Sir."
        )

    def think(self, prompt: str) -> dict:
        """Processes text queries and returns the response with latency telemetry."""
        t0 = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[self.system_instruction, prompt]
        )
        latency = time.time() - t0
        return {
            "text": response.text.strip(),
            "latency": round(latency, 2)
        }

    def see(self, image_path: str, prompt: str = "Analyze this visual feed.") -> dict:
        """Processes images from the GoPro camera."""
        t0 = time.time()
        image = Image.open(image_path)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[self.system_instruction, prompt, image]
        )
        latency = time.time() - t0
        return {
            "text": response.text.strip(),
            "latency": round(latency, 2)
        }

    def listen(self, audio_bytes: bytes, prompt_context: str = "") -> dict:
        """Processes raw microphone audio waveforms directly."""
        t0 = time.time()
        contents = [
            self.system_instruction,
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        ]
        if prompt_context:
            contents.append(prompt_context)
            
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents
        )
        latency = time.time() - t0
        return {
            "text": response.text.strip(),
            "latency": round(latency, 2)
        }

if __name__ == "__main__":
    print("\n--- INITIATING JARVIS COGNITIVE BRAIN TEST ---")
    brain = JarvisBrain()
    res = brain.think("Acknowledge system boot sequence on Windows 11 in one concise sentence.")
    print(f"[STATUS] Connected! Latency: {res['latency']}s")
    print(f"[JARVIS SAYS]: \"{res['text']}\"\n")
