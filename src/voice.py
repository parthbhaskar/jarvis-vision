import os
import time
import asyncio
import sounddevice as sd
from scipy.io.wavfile import write
import edge_tts
import pygame

class JarvisVoice:
    """Neural Voice Interface for Windows with Pygame playback."""

    def __init__(self, voice="en-GB-RyanNeural"):
        self.voice = voice
        self.sample_rate = 16000
        self.output_mp3 = os.path.expanduser("~\\jarvis_speech.mp3")
        self.input_wav = os.path.expanduser("~\\jarvis_input.wav")
        pygame.mixer.init()

    async def _synthesize(self, text: str):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate="+5%"
        )
        await communicate.save(self.output_mp3)

    def speak(self, text: str):
        """Synthesizes text using Microsoft Neural Voice and plays aloud."""
        print(f"\n[JARVIS SPEAKING]: \"{text}\"")
        try:
            asyncio.run(self._synthesize(text))
            pygame.mixer.music.load(self.output_mp3)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
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
    print("\n--- AUDITIONING JARVIS NEURAL VOICE (en-GB-RyanNeural) ---")
    voice = JarvisVoice()
    voice.speak("Neural voice synthesizer online on Windows 11. All core systems are standing by for your command, Sir.")
