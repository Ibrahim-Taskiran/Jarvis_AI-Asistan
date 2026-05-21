"""
core/brain.py - JARVIS LLM Beyin Modülü
Ollama üzerinden SIMPLE ve COMPLEX modellere bağlanarak
kullanıcı komutlarını JSON formatında analiz eder.
"""

import json
import logging
import ollama
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import SIMPLE_MODEL, COMPLEX_MODEL

logger = logging.getLogger(__name__)

# ── Sistem Promptu ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Sen JARVIS adlı Türkçe bir masaüstü asistansın.
Kullanıcının komutlarını analiz et ve YALNIZCA JSON döndür.

Eğer komut bir uygulama açma/kapama, sistem komutu, git işlemi, tarayıcı, medya veya dosya işlemi ise JSON döndür:
{"action": "<aksiyon>", "params": {<parametreler>}, "confirm": false}

Eğer komut bir sohbet, soru, selamlama veya belirsiz bir şeyse MUTLAKA şunu döndür:
{"action": "free_chat", "params": {}, "confirm": false}

"confirm: true" yalnızca tehlikeli işlemlerde kullanılır (shutdown, delete, force_push).

ÖRNEKLER:
"Merhaba nasılsın" → {"action": "free_chat", "params": {}, "confirm": false}
"Spotify aç" → {"action": "open_app", "params": {"app": "spotify"}, "confirm": false}
"Hava durumu" → {"action": "free_chat", "params": {}, "confirm": false}
"Sesi kıs" → {"action": "volume_control", "params": {"direction": "down"}, "confirm": false}
"Ne yapabilirsin?" → {"action": "free_chat", "params": {}, "confirm": false}
"Bilgisayarı kapat" → {"action": "shutdown", "params": {}, "confirm": true}
"Masaüstüne kalem isimli txt dosyası oluştur" → {"action": "free_chat", "params": {}, "confirm": false}
"Masaüstündeki test.txt dosyasını aç" → {"action": "free_chat", "params": {}, "confirm": false}
"Github Desktop aç" → {"action": "free_chat", "params": {}, "confirm": false}

Mevcut aksiyonlar:
- open_app        : Uygulama aç           → params: {"app": "spotify"}
- close_app       : Uygulama kapat        → params: {"app": "spotify"}
- shutdown        : Bilgisayarı kapat     → params: {}
- restart         : Bilgisayarı yeniden başlat → params: {}
- volume_control  : Ses seviyesi ayarla   → params: {"level": 50} veya {"action": "mute"}
- git_push        : Git push yap          → params: {"repo": "proje_adı", "message": "commit mesajı"}
- git_pull        : Git pull yap          → params: {"repo": "proje_adı"}
- git_status      : Git durumu göster     → params: {"repo": "proje_adı"}
- git_fetch       : Git fetch yap         → params: {"repo": "proje_adı"}
- run_terminal    : Terminal komutu çalıştır → params: {"command": "komut"}
- open_browser    : Tarayıcıda URL aç     → params: {"url": "https://..."}
- media_control   : Medya kontrol         → params: {"action": "play|pause|next|prev"}
- organize_files  : Dosyaları düzenle     → params: {"path": "klasör_yolu"}
- summarize_file  : Dosyayı özetle        → params: {"path": "dosya_yolu"}
- create_readme   : README oluştur        → params: {"repo": "proje_adı"}
- generate_prompt : Prompt üret           → params: {"topic": "konu"}
- daily_summary   : Günlük özet          → params: {}
- free_chat       : Sohbet / belirsiz     → params: {}

Kurallar:
1. YALNIZCA geçerli JSON döndür, başka metin ekleme.
2. Sohbet, selamlama, soru veya belirsiz komutlar için MUTLAKA "free_chat" aksiyonunu kullan.
3. Tehlikeli işlemlerde (shutdown, delete, force_push) "confirm": true yap.
4. Parametreleri Türkçe komuttan doğru şekilde çıkar.
"""


class Brain:
    """Ollama LLM bağlantısını yöneten JARVIS beyin modülü."""

    def __init__(self, use_complex: bool = False):
        """
        Brain başlatıcı.

        Args:
            use_complex: True ise COMPLEX_MODEL, False ise SIMPLE_MODEL kullanılır.
        """
        self.model = COMPLEX_MODEL if use_complex else SIMPLE_MODEL
        self.conversation_history: list[dict] = []
        logger.info(f"Brain başlatıldı → Model: {self.model}")

    def _build_messages(self, user_input: str) -> list[dict]:
        """Sistem promptu ve kullanıcı mesajını birleştirerek mesaj listesi oluşturur."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history,
            {"role": "user", "content": user_input},
        ]
        return messages

    def _extract_json(self, raw_response: str) -> dict | None:
        """
        LLM yanıtından JSON objesini çıkarır.
        Bazen model JSON'u markdown bloğu içinde döndürür, bunu da handle eder.
        """
        text = raw_response.strip()

        # Markdown kod bloğu varsa temizle
        if text.startswith("```"):
            lines = text.split("\n")
            # İlk ve son satırı (``` işaretlerini) kaldır
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # JSON parse et
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON bloğunu bulmaya çalış
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

        logger.warning(f"JSON parse edilemedi: {text[:200]}")
        return None

    # Tehlikeli aksiyonlar — bunlarda confirm her zaman True olmalı
    DANGEROUS_ACTIONS = {"shutdown", "restart", "force_push", "delete"}

    def _normalize_response(self, parsed: dict) -> dict:
        """
        LLM yanıtındaki eksik alanları varsayılan değerlerle tamamlar.
        Tehlikeli aksiyonlarda confirm=True olmasını garanti eder.
        """
        # Eksik alanları doldur
        if "params" not in parsed:
            parsed["params"] = {}
        if "confirm" not in parsed:
            parsed["confirm"] = False

        # Tehlikeli aksiyonlarda confirm'i zorla True yap
        action = parsed.get("action", "")
        if action in self.DANGEROUS_ACTIONS:
            parsed["confirm"] = True

        return parsed

    def think(self, user_input: str, context=None) -> dict | None:
        """
        Kullanıcı komutunu Ollama'ya gönderir ve JSON yanıt döndürür.

        Args:
            user_input: Kullanıcının sesli/yazılı komutu.

        Returns:
            Parsed JSON dict veya None (hata durumunda).
        """
        try:
            messages = self._build_messages(user_input)

            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.1,     # Düşük sıcaklık → tutarlı JSON
                    "num_predict": 256,      # Kısa yanıt yeterli
                },
            )

            raw_content = response["message"]["content"]
            logger.debug(f"Ham LLM yanıtı: {raw_content}")

            # Ollama yanıtı zaten dict olabilir, kontrol et
            if isinstance(raw_content, dict):
                parsed = raw_content
            elif isinstance(raw_content, str):
                parsed = self._extract_json(raw_content)
            else:
                parsed = self._extract_json(str(raw_content))

            if parsed:
                parsed = self._normalize_response(parsed)

                # Başarılı yanıtı konuşma geçmişine ekle
                self.conversation_history.append(
                    {"role": "user", "content": user_input}
                )
                self.conversation_history.append(
                    {"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)}
                )

                # Geçmişi son 10 mesajla sınırla (bellek tasarrufu)
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]

            return parsed

        except ollama.ResponseError as e:
            logger.error(f"Ollama yanıt hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Brain.think() hatası: {e}")
            return None

    def switch_model(self, use_complex: bool):
        """Model değiştir (basit ↔ karmaşık)."""
        old_model = self.model
        self.model = COMPLEX_MODEL if use_complex else SIMPLE_MODEL
        logger.info(f"Model değiştirildi: {old_model} → {self.model}")

    def clear_history(self):
        """Konuşma geçmişini temizle."""
        self.conversation_history.clear()
        logger.info("Konuşma geçmişi temizlendi.")

    def get_status(self) -> dict:
        """Brain durumunu döndür."""
        return {
            "model": self.model,
            "history_length": len(self.conversation_history),
            "simple_model": SIMPLE_MODEL,
            "complex_model": COMPLEX_MODEL,
        }
