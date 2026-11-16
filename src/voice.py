import os
import time
import uuid
import tempfile
import asyncio
import sounddevice as sd
from scipy.io.wavfile import write
import edge_tts
import pygame

class JarvisVoice:
    """Neural Voice Interface for Windows with Non-Locking Playback."""

    def __init__(self, voice="en-GB-RyanNeural"):
        self.voice = voice
        self.sample_rate = 16000
        self.temp_dir = tempfile.gettempdir()
        self.input_wav = os.path.join(self.temp_dir, "jarvis_input.wav")
        pygame.mixer.init()

    async def _synthesize(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate="+5%"
        )
        await communicate.save(output_path)

    def speak(self, text: str):
        """Synthesizes text using Microsoft Neural Voice and plays without file locks."""
        print(f"\n[JARVIS SPEAKING]: \"{text}\"")
        # Generate a unique temp file for each phrase to avoid Windows file locks
        unique_mp3 = os.path.join(self.temp_dir, f"jarvis_{uuid.uuid4().hex[:8]}.mp3")
        try:
            asyncio.run(self._synthesize(text, unique_mp3))
            pygame.mixer.music.load(unique_mp3)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            # Explicitly unload and release Windows file handle
            pygame.mixer.music.unload()
            try:
                os.remove(unique_mp3)
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR] Speech synthesis failed: {e}")

    def record_mic(self, duration: int = 4) -> bytes:
        """Records microphone input and returns WAV bytes for Gemini."""
        print("\n" + "="*45)
        print(f">>> LISTENING ({duration}s)... SPEAK TO JARVIS NOW <<<")
        print("="*45)
        
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        write(self.input_wav, self.sample_rate, recording)
        
        with open(self.input_wav, "rb") as f:
            return f.read()

if __name__ == "__main__":
    print("\n--- TESTING MULTI-TURN AUDIO PLAYBACK ---")
    v = JarvisVoice()
    v.speak("First sentence initialized cleanly.")
    v.speak("Second sentence played without file lock error. Voice subsystem is ready.")
