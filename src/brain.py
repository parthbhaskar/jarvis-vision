import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

class JarvisBrain:
    """Core Cognitive Engine with Conversational Context Memory."""

    def __init__(self, model_name="gemini-3.5-flash-lite"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.system_instruction = (
            "You are JARVIS, an advanced, highly capable personal AI assistant running on Windows 11. "
            "You have live visual access to a camera, full system control, and voice interaction. "
            "Address the user respectfully as Sir. Maintain conversational context across turns. "
            "Keep your answers concise, intelligent, and articulate."
        )
        self.history = []

    def think(self, prompt: str) -> dict:
        """Processes text with rolling multi-turn memory."""
        t0 = time.time()
        
        # Build prompt with rolling context
        self.history.append({"role": "user", "text": prompt})
        # Keep last 10 messages for fast inference
        recent_history = self.history[-10:]
        
        contents = [self.system_instruction]
        for msg in recent_history:
            contents.append(f"{msg['role'].upper()}: {msg['text']}")

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                reply = response.text.strip()
                self.history.append({"role": "assistant", "text": reply})
                return {"text": reply, "latency": round(time.time() - t0, 2)}
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                return {"text": "I experienced a momentary connection spike, Sir. Standing by.", "latency": round(time.time() - t0, 2)}

    def see(self, image_path: str, prompt: str = "Analyze this visual feed.") -> dict:
        """Multimodal visual reasoning over the active camera frame."""
        t0 = time.time()
        try:
            image = Image.open(image_path)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.system_instruction, prompt, image]
            )
            reply = response.text.strip()
            self.history.append({"role": "user", "text": "[User shared live camera frame]"})
            self.history.append({"role": "assistant", "text": reply})
            return {"text": reply, "latency": round(time.time() - t0, 2)}
        except Exception as e:
            return {"text": f"Visual processing error: {e}", "latency": round(time.time() - t0, 2)}

    def listen(self, audio_bytes: bytes, prompt_context: str = "") -> dict:
        """Acoustic waveform reasoning."""
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
            reply = response.text.strip()
            self.history.append({"role": "user", "text": "[User voice input]"})
            self.history.append({"role": "assistant", "text": reply})
            return {"text": reply, "latency": round(time.time() - t0, 2)}
        except Exception as e:
            return {"text": "Audio waveform analysis error, Sir.", "latency": round(time.time() - t0, 2)}
