"""
test_free_chat.py - free_chat modülü test scripti
Router, TTS is_speaking flag ve free_chat.execute() fonksiyonlarını test eder.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("  JARVIS Free Chat Modülü Test")
print("=" * 60)

# ── Test 1: Router fallback testi ──────────────────────────
print("\n── Test 1: Router fallback (unknown → free_chat) ──")
from core import router

result = router.route("unknown_action")
print(f"  route('unknown_action') → {result}")
assert result["module"] == "free_chat", "HATA: Bilinmeyen aksiyon free_chat'e yönlendirilmedi!"
assert result["model"] == "complex", "HATA: Model complex olmalı!"
print("  ✓ Bilinmeyen aksiyonlar free_chat modülüne yönlendiriliyor.")

# Bilinen aksiyonlar hâlâ doğru çalışmalı
result2 = router.route("open_app")
print(f"  route('open_app') → {result2}")
assert result2["module"] == "app_manager", "HATA: Bilinen aksiyon yanlış modüle yönlendirildi!"
print("  ✓ Bilinen aksiyonlar doğru modüle yönlendiriliyor.")

# ── Test 2: TTS is_speaking flag ──────────────────────────
print("\n── Test 2: TTS is_speaking flag ──")
from core.tts import TTS

tts = TTS()
print(f"  Başlangıç is_speaking: {tts.is_speaking}")
assert tts.is_speaking == False, "HATA: is_speaking başlangıçta False olmalı!"
print("  ✓ is_speaking başlangıçta False.")

tts.stop()
print(f"  stop() sonrası is_speaking: {tts.is_speaking}")
assert tts.is_speaking == False, "HATA: stop() sonrası is_speaking False olmalı!"
print("  ✓ stop() is_speaking'i False yapıyor.")

# ── Test 3: free_chat modülü import testi ──────────────────
print("\n── Test 3: free_chat modülü import ──")
from modules import free_chat

print(f"  free_chat.execute fonksiyonu: {free_chat.execute}")
print("  ✓ free_chat modülü başarıyla import edildi.")

# ── Test 4: free_chat.execute() - Dosya oluşturma ─────────
print("\n── Test 4: Dosya oluşturma testi ──")
result = free_chat.execute("Masaüstüne kalem isimli txt dosyası oluştur")
print(f"  Sonuç: {result}")
if result["success"]:
    desktop = os.path.expanduser("~\\Desktop")
    expected_file = os.path.join(desktop, "kalem.txt")
    if os.path.exists(expected_file):
        print(f"  ✓ Dosya oluşturuldu: {expected_file}")
    else:
        print(f"  ⚠ Dosya beklenen yerde bulunamadı: {expected_file}")
else:
    print(f"  ✗ Dosya oluşturulamadı: {result['message']}")

# ── Test 5: free_chat.execute() - Arama algılama ──────────
print("\n── Test 5: Arama algılama testi ──")
result = free_chat.execute("Elazığ hava durumu ara")
print(f"  Sonuç: {result}")
if result["success"]:
    print("  ✓ Arama başarıyla açıldı.")
else:
    print(f"  ⚠ Arama hatası: {result['message']}")

# ── Test 6: free_chat.execute() - Sohbet (Mistral 7B) ─────
print("\n── Test 6: Sohbet testi - 'Merhaba nasılsın?' ──")
result = free_chat.execute("Merhaba nasılsın?")
print(f"  Sonuç: {result}")
if result["success"]:
    print(f"  ✓ LLM yanıtı: {result['message'][:200]}")
else:
    print(f"  ⚠ Sohbet hatası: {result['message']}")

# ── Test 7: Takip sorusu ──────────────────────────────────
print("\n── Test 7: Takip sorusu - 'Peki sen ne yapabilirsin?' ──")
result = free_chat.execute("Peki sen ne yapabilirsin?")
print(f"  Sonuç: {result}")
if result["success"]:
    print(f"  ✓ LLM yanıtı: {result['message'][:200]}")
else:
    print(f"  ⚠ Sohbet hatası: {result['message']}")

# ── Test 8: Listener interrupt desteği testi ───────────────
print("\n── Test 8: Listener interrupt desteği ──")
from core.listener import Listener
import inspect

sig = inspect.signature(Listener.start_listening)
params = list(sig.parameters.keys())
print(f"  start_listening parametreleri: {params}")
assert "tts" in params, "HATA: tts parametresi bulunamadı!"
print("  ✓ Listener.start_listening() tts parametresi kabul ediyor.")

# ── Özet ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  Tüm testler tamamlandı!")
print("=" * 60)
