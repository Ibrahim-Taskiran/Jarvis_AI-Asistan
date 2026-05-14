"""
core/listener.py - JARVIS Ses Dinleyici Modülü
faster-whisper + sounddevice ile mikrofondan Türkçe sesli komut tanıma.
Sessizlik tespiti, uyku modu ve sürekli dinleme desteği.
"""

import logging
import threading
import time
import numpy as np
import sounddevice as sd
import sys
import os
import io
import tempfile
import wave

from faster_whisper import WhisperModel

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import WHISPER_MODEL, WHISPER_LANGUAGE

logger = logging.getLogger(__name__)

# ── Ses Ayarları ─────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Whisper 16kHz bekler
CHANNELS = 1                 # Mono
CHUNK_DURATION = 3           # Her chunk 3 saniye
SILENCE_THRESHOLD = 0.01     # Bu seviyenin altı sessizlik sayılır
MAX_RECORD_SECONDS = 10      # Maksimum kayıt süresi (ses varsa)
MIN_AUDIO_LENGTH = 0.5       # Minimum ses uzunluğu (saniye)


class Listener:
    """
    Mikrofondan ses dinleyip faster-whisper ile Türkçe metin tanıma yapan modül.

    Özellikler:
        - 3 saniyelik chunk'lar halinde dinleme
        - Sessizlik tespiti (threshold altı = işleme almaz)
        - Uyku modu (pause/resume)
        - Sürekli dinleme döngüsü (start_listening)
    """

    def __init__(self, device: str = "cuda"):
        """
        Listener başlatıcı.

        Args:
            device: Whisper çalışma cihazı ("cuda" veya "cpu").
        """
        self.device = device
        self.sample_rate = SAMPLE_RATE
        self.channels = CHANNELS
        self.chunk_duration = CHUNK_DURATION
        self.silence_threshold = SILENCE_THRESHOLD

        self._paused = False
        self._stop_event = threading.Event()
        self._listen_thread: threading.Thread | None = None

        # Whisper modelini yükle (CUDA başarısız olursa CPU'ya düş)
        logger.info(f"Whisper model yükleniyor: {WHISPER_MODEL} (device={device})")
        try:
            self.model = WhisperModel(
                WHISPER_MODEL,
                device=device,
                compute_type="float16" if device == "cuda" else "int8",
            )
            # Hızlı doğrulama — CUDA runtime sorunlarını erken yakala
            if device == "cuda":
                import numpy as _np
                _test = _np.zeros(16000, dtype=_np.float32)
                list(self.model.transcribe(_test, language=WHISPER_LANGUAGE))
        except Exception as e:
            if device == "cuda":
                logger.warning(f"CUDA başarısız ({e}), CPU moduna geçiliyor...")
                self.device = "cpu"
                self.model = WhisperModel(
                    WHISPER_MODEL,
                    device="cpu",
                    compute_type="int8",
                )
            else:
                raise
        logger.info(f"Whisper model hazır (device={self.device}).")

    def _is_silent(self, audio_data: np.ndarray) -> bool:
        """Ses verisinin sessizlik eşiğinin altında olup olmadığını kontrol eder."""
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms < self.silence_threshold

    def _record_chunk(self, duration: float = None) -> np.ndarray:
        """
        Mikrofondan belirtilen süre kadar ses kaydeder.

        Args:
            duration: Kayıt süresi (saniye). None ise chunk_duration kullanılır.

        Returns:
            numpy array olarak ses verisi.
        """
        if duration is None:
            duration = self.chunk_duration

        frames = int(duration * self.sample_rate)
        logger.debug(f"Kayıt başlıyor: {duration}s, {frames} frame")

        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()  # Kayıt bitene kadar bekle

        return audio.flatten()

    def _transcribe(self, audio_data: np.ndarray) -> str:
        """
        Ses verisini Whisper ile metne çevirir.

        Args:
            audio_data: float32 numpy array (16kHz, mono).

        Returns:
            Tanınan metin (boş string olabilir).
        """
        try:
            segments, info = self.model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                beam_size=5,
                vad_filter=True,           # Sessiz bölümleri otomatik filtrele
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )

            text = " ".join(segment.text.strip() for segment in segments).strip()

            if text:
                logger.info(f"Tanınan metin: '{text}'")

            return text

        except Exception as e:
            logger.error(f"Transcribe hatası: {e}")
            return ""

    def listen(self) -> str:
        """
        Mikrofonu bir kez dinler ve tanınan metni döndürür.

        Süreç:
        1. 3 saniyelik chunk kaydeder
        2. Sessizlik kontrolü yapar
        3. Ses varsa Whisper'a gönderir
        4. Tanınan metni döndürür

        Returns:
            Tanınan Türkçe metin veya boş string.
        """
        if self._paused:
            logger.debug("Listener duraklatılmış, dinleme atlanıyor.")
            return ""

        # Ses kaydı
        audio = self._record_chunk()

        # Sessizlik kontrolü
        if self._is_silent(audio):
            logger.debug("Sessizlik tespit edildi, işleme alınmıyor.")
            return ""

        # Minimum uzunluk kontrolü
        audio_length = len(audio) / self.sample_rate
        if audio_length < MIN_AUDIO_LENGTH:
            logger.debug(f"Ses çok kısa: {audio_length:.2f}s")
            return ""

        # Whisper ile metin tanıma
        return self._transcribe(audio)

    def start_listening(self, callback: callable):
        """
        Sürekli dinleme döngüsü başlatır. Her başarılı tanımada callback(text) çağırır.

        Args:
            callback: Tanınan metin ile çağrılacak fonksiyon → callback(text: str)
        """
        self._stop_event.clear()
        logger.info("Sürekli dinleme başlatılıyor...")

        def _loop():
            while not self._stop_event.is_set():
                if self._paused:
                    time.sleep(0.5)
                    continue

                text = self.listen()
                if text:
                    try:
                        callback(text)
                    except Exception as e:
                        logger.error(f"Callback hatası: {e}")

            logger.info("Dinleme döngüsü durduruldu.")

        self._listen_thread = threading.Thread(target=_loop, daemon=True)
        self._listen_thread.start()
        logger.info("Dinleme thread'i başlatıldı.")

    def stop_listening(self):
        """Sürekli dinleme döngüsünü durdurur."""
        self._stop_event.set()
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=5)
        self._listen_thread = None
        logger.info("Dinleme durduruldu.")

    def pause(self):
        """Dinlemeyi duraklatır (uyku modu)."""
        self._paused = True
        logger.info("Listener duraklatıldı (uyku modu).")

    def resume(self):
        """Dinlemeyi devam ettirir (uyku modundan çık)."""
        self._paused = False
        logger.info("Listener devam ettiriliyor.")

    @property
    def is_paused(self) -> bool:
        """Listener'ın duraklatılmış olup olmadığını döndürür."""
        return self._paused

    @property
    def is_listening(self) -> bool:
        """Sürekli dinleme döngüsünün aktif olup olmadığını döndürür."""
        return self._listen_thread is not None and self._listen_thread.is_alive()

    def get_status(self) -> dict:
        """Listener durumunu döndürür."""
        return {
            "model": WHISPER_MODEL,
            "language": WHISPER_LANGUAGE,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "chunk_duration": self.chunk_duration,
            "silence_threshold": self.silence_threshold,
            "paused": self._paused,
            "listening": self.is_listening,
        }
