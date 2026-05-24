"""
Hizli listener testi - mikrofonu 1 kez dinleyip sonucu ekrana basar.
Kullanim:  python tests/test_listener_quick.py
"""

import sys, os, logging

# Proje kokunu path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Windows konsol encoding sorunu icin
sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from core.listener import Listener

print("=" * 60)
print("JARVIS Listener Testi")
print("Model: medium (CTranslate2) | Dil: tr (forced)")
print("Gurultu azaltma: noisereduce + 80Hz high-pass filtre")
print("Headset optimizasyonu: blocksize=1024")
print("=" * 60)
print()

listener = Listener(device="cpu")

print("Mikrofonunuza Turkce bir cumle soyleyin...")
print("(Ornek: 'Jarvis, Spotify'i ac ve GitHub reposunu kontrol et')")
print(">> 10 saniye icinde konusun, 1.5 sn sessizlikte kayit biter.")
print()

text = listener.listen()

print()
print("=" * 60)
if text:
    print(f"[OK] Taninan metin: <<{text}>>")
else:
    print("[--] Ses algilanamadi veya sessizlik tespit edildi.")
    print("     Tekrar deneyin ve mikrofona yakin konusun.")
print("=" * 60)
