"""
test_listener.py - Listener modulu mikrofon testi
Mikrofonu 2 kez dinler ve tanınan metni gosterir.
Kullanici: "Spotify'i ac" ve "GitHub'a yukle" soylesin.
"""

import sys
import io
import time

# Windows konsol encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from core.listener import Listener


def main():
    print("=" * 60)
    print("  JARVIS Listener Modulu - Mikrofon Testi")
    print("=" * 60)

    # 1. Listener baslat
    print("\n[INFO] Whisper model yukleniyor (ilk seferde indirme olabilir)...")
    listener = Listener(device="cuda")

    status = listener.get_status()
    print(f"[OK] Listener hazir!")
    print(f"   Model     : {status['model']}")
    print(f"   Dil       : {status['language']}")
    print(f"   Cihaz     : {status['device']}")
    print(f"   Ornekleme : {status['sample_rate']} Hz")
    print(f"   Chunk     : {status['chunk_duration']}s")

    # 2. Iki kez dinle
    test_commands = [
        "Spotify'i ac",
        "GitHub'a yukle",
    ]

    for i, expected in enumerate(test_commands, 1):
        print(f"\n{'─' * 60}")
        print(f"  Test {i}/2: Lutfen mikrofona soyleyin: \"{expected}\"")
        print(f"  (3 saniye kayit yapilacak...)")
        print(f"{'─' * 60}")

        time.sleep(1)  # Kullaniciya okuma zamani
        print("  [REC] Dinleniyor...")

        text = listener.listen()

        if text:
            print(f"  [OK] Taninan metin: \"{text}\"")
        else:
            print(f"  [--] Ses taninamadi veya sessizlik tespit edildi.")
            print(f"       Tekrar deneyelim...")
            time.sleep(0.5)
            print("  [REC] Tekrar dinleniyor...")
            text = listener.listen()
            if text:
                print(f"  [OK] Taninan metin: \"{text}\"")
            else:
                print(f"  [FAIL] Yine taninamadi. Mikrofonu kontrol edin.")

    # 3. Pause/Resume testi
    print(f"\n{'─' * 60}")
    print("  Pause/Resume Testi")
    print(f"{'─' * 60}")

    listener.pause()
    print(f"  [PAUSE] Paused: {listener.is_paused}")

    paused_result = listener.listen()
    print(f"  [TEST] Paused durumda listen() sonucu: '{paused_result}' (bos olmali)")

    listener.resume()
    print(f"  [RESUME] Paused: {listener.is_paused}")

    pause_ok = paused_result == "" and not listener.is_paused
    print(f"  [{'PASS' if pause_ok else 'FAIL'}] Pause/Resume calisiyor: {pause_ok}")

    print(f"\n{'=' * 60}")
    print(f"  Test tamamlandi.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
