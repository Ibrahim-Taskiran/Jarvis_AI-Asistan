"""
Hızlı Jest Yöneticisi Testi - 6 hareketi test etmek için.
Kullanım:  python tests/test_gesture_manager_quick.py
"""

import sys, os, time, logging

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from modules.gesture_manager import GestureManager

print("=" * 60)
print("JARVIS Jest Yöneticisi Testi")
print("Desteklenen 6 Jest:")
print("  1. OPEN_PALM        -> Space (Play/Pause)")
print("  2. FIST             -> Alt + F4 (Close Tab/Window)")
print("  3. THUMBS_UP        -> Ctrl + Up & Volume Up (pycaw)")
print("  4. THUMBS_DOWN      -> Ctrl + Down & Volume Down (pycaw)")
print("  5. INDEX_UP         -> Scroll Up (300)")
print("  6. BOTH_FISTS_CROSS -> Win + D (Minimize Windows)")
print("=" * 60)
print()
print("Kamera başlatılıyor... Önizleme penceresinden el hareketlerinizi gösterin.")
print("Çıkmak için önizleme penceresindeyken 'q' tuşuna basın.")
print()

manager = GestureManager()
res = manager.start()

try:
    while manager.is_running:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Durduruluyor...")
finally:
    manager.stop()
    print("Test sonlandırıldı.")
