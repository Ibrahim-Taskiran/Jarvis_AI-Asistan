"""
test_listener_interactive.py - Interaktif Mikrofon Testi
Kullanici mikrofona konusur, taninan metni gosterir.
Cikmak icin Ctrl+C basin.
"""

import sys
import os
import time

# Unbuffered stdout
os.environ["PYTHONUNBUFFERED"] = "1"

def log(msg):
    """Flush garantili print."""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def on_command(text):
    """Her basarili ses tanimadiginda cagrilir."""
    log(f"\n  >>> Taninan: \"{text}\"\n")
    log("  [REC] Dinleniyor... (Ctrl+C ile cikin)")


def main():
    log("=" * 60)
    log("  JARVIS - Interaktif Mikrofon Testi")
    log("  Mikrofona konusun, taninan metin gorunecek.")
    log("  Cikmak icin Ctrl+C basin.")
    log("=" * 60)

    log("\n[INFO] Whisper model yukleniyor (CPU, int8)...")

    from core.listener import Listener
    listener = Listener(device="cpu")

    log(f"[OK] Hazir! Device: {listener.device}")
    log("")
    log("  [REC] Dinleniyor... (Ctrl+C ile cikin)")

    try:
        listener.start_listening(callback=on_command)

        # Ana thread'i canli tut
        while True:
            time.sleep(0.5)

    except KeyboardInterrupt:
        log("\n\n[STOP] Dinleme durduruluyor...")
        listener.stop_listening()
        log("[OK] Cikis yapildi.")


if __name__ == "__main__":
    main()
