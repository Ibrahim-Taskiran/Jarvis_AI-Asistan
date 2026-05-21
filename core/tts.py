"""
core/tts.py - Metin okuma (Text-to-Speech) Modülü
Piper TTS motorunu kullanır. Piper bulunamazsa pyttsx3'e düşer.
"""

import os
import time
import logging
import threading
import subprocess
import tempfile
import pyttsx3

try:
    import winsound
except ImportError:
    winsound = None

logger = logging.getLogger(__name__)

# Base path for Piper
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PIPER_EXE = os.path.join(BASE_DIR, "piper", "piper.exe")
VOICE_MODEL = os.path.join(BASE_DIR, "piper", "voices", "tr_TR-dfki-medium.onnx")

class TTS:
    """Piper TTS veya fallback olarak pyttsx3 ile metinleri sese dönüştürür."""
    
    def __init__(self):
        self.use_piper = os.path.exists(PIPER_EXE) and os.path.exists(VOICE_MODEL)
        self._current_process = None
        self._stop_event = threading.Event()
        self.is_speaking = False
        
        if self.use_piper:
            logger.info("TTS Motoru: Piper (tr_TR-dfki-medium)")
        else:
            logger.warning("Piper bulunamadı! Fallback olarak pyttsx3 başlatılıyor.")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            tr_voice = None
            for voice in voices:
                if 'turkish' in voice.name.lower() or 'tr' in voice.languages:
                    tr_voice = voice.id
                    break
            if tr_voice:
                self.engine.setProperty('voice', tr_voice)
            else:
                logger.warning("Türkçe ses bulunamadı, varsayılan ses kullanılıyor.")
            self.engine.setProperty('rate', 150)
        except Exception as e:
            logger.error(f"pyttsx3 başlatılamadı: {e}")
            self.engine = None

    def speak(self, text: str):
        """Metni senkron olarak okur."""
        if not text:
            return
            
        self._stop_event.clear()
        self.is_speaking = True
        
        if self.use_piper and winsound:
            temp_wav = ""
            try:
                temp_wav = os.path.join(tempfile.gettempdir(), f"piper_tts_{int(time.time() * 1000)}.wav")
                
                # Piper process'ini başlat
                self._current_process = subprocess.Popen(
                    [PIPER_EXE, "--model", VOICE_MODEL, "--output_file", temp_wav],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                self._current_process.communicate(input=text.encode('utf-8'))
                
                if self._stop_event.is_set():
                    self.is_speaking = False
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)
                    return
                    
                if os.path.exists(temp_wav):
                    # Çal
                    winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            except Exception as e:
                logger.error(f"Piper TTS hatası: {e}. pyttsx3 deneniyor...")
                self._fallback_speak(text)
            finally:
                self.is_speaking = False
                # Geçici dosyayı sil
                if temp_wav and os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except Exception as e:
                        logger.debug(f"Geçici wav silinemedi: {e}")
        else:
            self._fallback_speak(text)

    def _fallback_speak(self, text: str):
        """pyttsx3 kullanarak metni okur."""
        if not hasattr(self, 'engine') or not self.engine:
            logger.error("Hiçbir TTS motoru kullanılamıyor.")
            return
            
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 okuma hatası: {e}")

    def speak_async(self, text: str):
        """Metni ayrı bir thread'de asenkron olarak okur."""
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    def stop(self):
        """Çalınan sesi veya çalışan okuma işlemini durdurur."""
        self._stop_event.set()
        self.is_speaking = False
        
        # Piper process'ini sonlandır
        if self._current_process:
            try:
                if self._current_process.poll() is None:
                    self._current_process.kill()  # Hemen öldür (immediate kill)
            except Exception as e:
                logger.debug(f"Piper sonlandırılamadı: {e}")
                
        # Winsound çalmayı durdur
        if self.use_piper and winsound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception as e:
                logger.debug(f"Winsound durdurulamadı: {e}")
            
        # pyttsx3 durdur
        if hasattr(self, 'engine') and self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
