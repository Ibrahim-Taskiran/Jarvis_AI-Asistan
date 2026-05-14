"""
core/tts.py - JARVIS Metin-Konuşma (TTS) Modülü
pyttsx3 ile tamamen yerel, Türkçe destekli TTS.
Kuyruk sistemi ile çakışmasız konuşma.
"""

import logging
import threading
import queue
import pyttsx3

logger = logging.getLogger(__name__)

SPEECH_RATE = 150


class TTS:
    """pyttsx3 tabanlı yerel TTS motoru. Thread-safe kuyruk sistemi."""

    def __init__(self):
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._engine_lock = threading.Lock()

        # Worker thread'i başlat (engine bu thread'de yaşar)
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        logger.info("TTS başlatıldı.")

    def _init_engine(self) -> pyttsx3.Engine:
        """pyttsx3 engine'i oluştur ve Türkçe sesi ayarla."""
        engine = pyttsx3.init()
        engine.setProperty("rate", SPEECH_RATE)

        # Türkçe ses ara
        voices = engine.getProperty("voices")
        turkish_voice = None
        for v in voices:
            langs = getattr(v, "languages", [])
            name_lower = v.name.lower() if v.name else ""
            id_lower = v.id.lower() if v.id else ""

            if any("tr" in str(l).lower() for l in langs) \
               or "turkish" in name_lower \
               or "tolga" in name_lower \
               or "tr-tr" in id_lower \
               or "turkish" in id_lower:
                turkish_voice = v
                break

        if turkish_voice:
            engine.setProperty("voice", turkish_voice.id)
            logger.info(f"Türkçe ses seçildi: {turkish_voice.name}")
        else:
            logger.warning("Türkçe ses bulunamadı, varsayılan ses kullanılıyor.")

        return engine

    def _worker(self):
        """Kuyruktan metin alıp sırayla okuyan arka plan worker'ı."""
        engine = self._init_engine()

        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if text is None:  # Poison pill → çık
                break

            try:
                logger.debug(f"TTS okuyor: '{text}'")
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS hatası: {e}")
            finally:
                self._queue.task_done()

        engine.stop()
        logger.info("TTS worker durduruldu.")

    def speak(self, text: str):
        """Metni sesli okur, bitene kadar bekler."""
        self._queue.put(text)
        self._queue.join()

    def speak_async(self, text: str):
        """Metni kuyruğa ekler, bloklamaz."""
        self._queue.put(text)

    def stop(self):
        """TTS'i durdurur ve worker'ı kapatır."""
        self._stop_event.set()
        self._queue.put(None)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        logger.info("TTS durduruldu.")

    def get_status(self) -> dict:
        return {
            "rate": SPEECH_RATE,
            "queue_size": self._queue.qsize(),
            "running": self._worker_thread.is_alive() if self._worker_thread else False,
        }
