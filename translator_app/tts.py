# ===================== TEXT-TO-SPEECH =====================
# Synthesizes speech with gTTS and plays it with pygame on a background thread.

import os
import time
import tempfile
import threading
import pygame
from gtts import gTTS
from .config import TTS_MAX_WAIT_SECONDS
from .languages import AUTO


class TextToSpeech:
    def __init__(self):
        self._available = False
        self._lock = threading.Lock()  # only one clip plays on the shared channel
        self._generation = 0           # newest request wins; older ones bow out
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._available = pygame.mixer.get_init() is not None
        except Exception as e:
            # no audio device (e.g. headless); speaking becomes a no-op
            print(f"Audio playback unavailable: {e}")

    def stop(self):
        # supersede any in-flight request and silence current playback
        self._generation += 1
        if self._available and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def speak(self, text, lang_code, on_error=None):
        # validate on the calling thread, then do network + audio work in the background
        if not text or not lang_code or lang_code == AUTO:
            if on_error:
                on_error("Language not supported for speech")
            return
        if not self._available:
            if on_error:
                on_error("Audio playback is not available")
            return

        self.stop()  # supersede and silence any current playback
        generation = self._generation
        threading.Thread(
            target=self._run, args=(text, lang_code, generation, on_error), daemon=True
        ).start()

    def _run(self, text, lang_code, generation, on_error):
        path = None
        try:
            # synthesis is a network call, so keep it outside the playback lock
            fd, path = tempfile.mkstemp(prefix="tts_", suffix=".mp3")
            os.close(fd)
            gTTS(text=text, lang=lang_code).save(path)

            with self._lock:
                if generation != self._generation:
                    return  # a newer request superseded this one
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                start = time.time()
                while pygame.mixer.music.get_busy():
                    if generation != self._generation:
                        pygame.mixer.music.stop()
                        break
                    if time.time() - start > TTS_MAX_WAIT_SECONDS:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.1)
                try:
                    pygame.mixer.music.unload()  # release the file before deleting it
                except Exception:
                    pass
        except Exception as e:
            message = str(e)
            if "language not supported" in message.lower():
                message = "Speech is not supported for this language"
            if on_error:
                on_error(f"Speech error: {message}")
        finally:
            self._remove(path)

    @staticmethod
    def _remove(path):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
