import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

class JarvisBrain:
    """Resilient Cognitive Engine with Traffic Spike Safeguards."""

    def __init__(self, model_name="gemini-3.5-flash-lite"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.system_instruction = (
            "You are JARVIS, an advanced personal AI systems assistant on Windows 11. "
            "Communicate concisely, professionally, and address the user respectfully as Sir."
        )

    def think(self, prompt: str) -> dict:
        t0 = time.time()
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[self.system_instruction, prompt]
                )
                return {"text": response.text.strip(), "latency": round(time.time() - t0, 2)}
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                return {"text": "I experienced a temporary cloud connection latency, Sir. Please repeat your command.", "latency": round(time.time() - t0, 2)}

    def see(self, image_path: str, prompt: str = "Analyze this visual feed.") -> dict:
        t0 = time.time()
        try:
            image = Image.open(image_path)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.system_instruction, prompt, image]
            )
            return {"text": response.text.strip(), "latency": round(time.time() - t0, 2)}
        except Exception as e:
            return {"text": f"Optical analysis error: {e}", "latency": round(time.time() - t0, 2)}

    def listen(self, audio_bytes: bytes, prompt_context: str = "") -> dict:
        t0 = time.time()
        try:
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
            return {"text": response.text.strip(), "latency": round(time.time() - t0, 2)}
        except Exception as e:
            return {"text": "I had difficulty parsing the audio waveform, Sir.", "latency": round(time.time() - t0, 2)}
