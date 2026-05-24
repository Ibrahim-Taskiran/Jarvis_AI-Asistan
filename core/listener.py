"""
core/listener.py - JARVIS Ses Dinleyici Modülü
faster-whisper + sounddevice ile mikrofondan Türkçe sesli komut tanıma.
Sessizlik tespiti, uyku modu ve sürekli dinleme desteği.
"""

import logging
import threading
import time
import re
import numpy as np
import sounddevice as sd
import sys
import os
import io
import tempfile
import wave

import noisereduce as nr
from scipy.signal import butter, sosfilt
from faster_whisper import WhisperModel

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import WHISPER_MODEL, WHISPER_LANGUAGE

logger = logging.getLogger(__name__)

# ── Ses Ayarları ─────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Whisper 16kHz bekler
CHANNELS = 1                 # Mono
CHUNK_DURATION = 5           # Her chunk 5 saniye
SILENCE_THRESHOLD = 0.003     # AMD mic array düşük seviyeli — 0.003 eşiği konuşmayı yakalar
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

        # Whisper modelini yükle — Türkçe için medium (CTranslate2 formatı)
        logger.info(f"Whisper model yükleniyor: medium (device={device})")
        self.model = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8",
        )
        logger.info("Whisper model hazır (device=cpu).")

    @staticmethod
    def _highpass_filter(audio: np.ndarray, sr: int, cutoff: float = 80.0) -> np.ndarray:
        """80 Hz altını kesen yüksek-geçiren (high-pass) Butterworth filtresi."""
        sos = butter(5, cutoff, btype="high", fs=sr, output="sos")
        return sosfilt(sos, audio).astype(np.float32)

    def _is_silent(self, audio_data: np.ndarray) -> bool:
        """Ses verisinin sessizlik eşiğinin altında olup olmadığını kontrol eder."""
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms < self.silence_threshold

    def _record_chunk(self, duration: float = None) -> np.ndarray:
        """
        Mikrofondan dinamik olarak ses kaydeder.
        Eğer konuşma başlarsa, konuşma bitene (1.5 sn sessizlik olana) veya 
        maksimum süreye (örn. 10 sn) ulaşana kadar kaydı uzatır.
        """
        if duration is None:
            duration = self.chunk_duration

        sample_rate = self.sample_rate
        chunk_size = int(0.1 * sample_rate)  # 100ms slices
        
        audio_buffer = []
        speech_detected = False
        silence_seconds = 0.0
        total_seconds = 0.0
        
        logger.debug("Dinamik kayıt başlıyor...")
        
        # Start input stream
        with sd.InputStream(samplerate=sample_rate, channels=self.channels, dtype="float32", blocksize=1024) as stream:
            while total_seconds < MAX_RECORD_SECONDS:
                # Read 100ms chunk
                data, overflowed = stream.read(chunk_size)
                flat_data = data.flatten()
                audio_buffer.append(flat_data)
                
                total_seconds += 0.1
                
                # Check silence/speech in this slice
                is_silent_slice = np.sqrt(np.mean(flat_data ** 2)) < self.silence_threshold
                
                if not speech_detected:
                    if not is_silent_slice:
                        speech_detected = True
                        logger.debug("Konuşma algılandı, kayıt uzatılıyor...")
                    elif total_seconds >= duration:
                        # If no speech detected after chunk_duration (5s), stop and return
                        break
                else:
                    if is_silent_slice:
                        silence_seconds += 0.1
                    else:
                        silence_seconds = 0.0
                        
                    # Stop if 1.5 seconds of continuous silence after speech detected
                    if silence_seconds >= 1.5:
                        logger.debug("1.5 saniye sessizlik algılandı, kayıt sonlandırılıyor.")
                        break
                        
        if not audio_buffer:
            return np.array([], dtype="float32")

        audio_np = np.concatenate(audio_buffer)

        # ── Gürültü azaltma (noisereduce) ────────────────────────────────────
        audio_np = nr.reduce_noise(
            y=audio_np, sr=sample_rate, stationary=False, prop_decrease=0.75
        )

        # ── Yüksek-geçiren filtre — 80 Hz altı düşük frekans gürültüsünü keser
        audio_np = self._highpass_filter(audio_np, sr=sample_rate, cutoff=80.0)

        return audio_np

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
                language="tr",
                task="transcribe",
                initial_prompt=(
                    "Bu bir Türkçe sesli komut uygulamasıdır. "
                    "Kullanıcı Türkçe komutlar vermektedir. "
                    "Uygulama adları, Git komutları ve dosya isimleri içerebilir."
                ),
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=1500,
                    speech_pad_ms=400,
                ),
                beam_size=5,
                best_of=5,
                temperature=0.0,
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

    def start_listening(self, callback: callable, tts=None):
        """
        Sürekli dinleme döngüsü başlatır. Her başarılı tanımada callback(text) çağırır.
        Eğer tts referansı verilmişse, konuşma sırasında yeni ses algılandığında
        konuşmayı kesip yeni komutu işler (interrupt desteği).

        Args:
            callback: Tanınan metin ile çağrılacak fonksiyon → callback(text: str)
            tts: TTS referansı (interrupt desteği için opsiyonel).
        """
        self._tts_ref = tts
        self._stop_event.clear()
        logger.info("Sürekli dinleme başlatılıyor...")

        def _loop():
            while not self._stop_event.is_set():
                if self._paused:
                    time.sleep(0.5)
                    continue

                try:
                    text = self.listen()
                    if text:
                        # ── 3) Durdurma Kelimeleri Kontrolü ──────────────────────────
                        lower_text = text.lower().strip().strip(".,?!;:")
                        stop_words = ["dur", "yeter", "yeterli", "stop", "enough", "quiet"]
                        has_stop_word = any(re.search(rf"\b{w}\b", lower_text) for w in stop_words)
                        
                        if has_stop_word:
                            logger.info(f"Durdurma komutu algılandı: '{text}'. Konuşma sonlandırılıyor.")
                            if self._tts_ref:
                                self._tts_ref.stop()
                            continue  # Komut işlemeyi atla (skip command processing)

                        # Interrupt: konuşma sırasında yeni ses algılandıysa konuşmayı kes
                        if self._tts_ref and self._tts_ref.is_speaking:
                            logger.info(f"Konuşma kesiliyor, yeni komut algılandı: '{text}'")
                            self._tts_ref.stop()

                        try:
                            callback(text)
                        except Exception as e:
                            logger.error(f"Callback hatası: {e}")
                except Exception as e:
                    logger.error(f"Dinleme döngüsü hatası (otomatik yeniden denenecek): {e}")
                    time.sleep(1.0)

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
