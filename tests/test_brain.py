"""
test_brain.py - Brain modulu hizli dogrulama testi
Ollama llama3.2:3b modeline "Spotify'i ac" komutu gonderir
ve gecerli bir JSON yanit aldigini dogrular.
"""

import sys
import os
import io
import json

# Windows konsol encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Brain modulunu import et
from core.brain import Brain


def main():
    print("=" * 60)
    print("  JARVIS Brain Modulu - Test")
    print("=" * 60)

    # 1. Brain'i SIMPLE model ile baslat
    brain = Brain(use_complex=False)
    status = brain.get_status()
    print(f"\n[OK] Brain baslatildi")
    print(f"   Model    : {status['model']}")
    print(f"   Basit    : {status['simple_model']}")
    print(f"   Karmasik : {status['complex_model']}")

    # 2. Test komutu gonder
    test_command = "Spotify'i ac"
    print(f"\n[SEND] Komut gonderiliyor: \"{test_command}\"")
    print("   Ollama'dan yanit bekleniyor...\n")

    result = brain.think(test_command)

    # 3. Sonucu degerlendir
    if result is None:
        print("[FAIL] BASARISIZ: JSON yanit alinamadi!")
        sys.exit(1)

    print(f"[RECV] Alinan JSON yanit:")
    print(f"   {json.dumps(result, ensure_ascii=False, indent=2)}")

    # 4. Yapi dogrulama
    errors = []
    if "action" not in result:
        errors.append("'action' alani eksik")
    if "params" not in result:
        errors.append("'params' alani eksik")
    if "confirm" not in result:
        errors.append("'confirm' alani eksik")

    if result.get("action") != "open_app":
        errors.append(f"Beklenen action: 'open_app', Alinan: '{result.get('action')}'")

    if result.get("params", {}).get("app", "").lower() != "spotify":
        errors.append(f"Beklenen app: 'spotify', Alinan: '{result.get('params', {}).get('app')}'")

    if result.get("confirm") is not False:
        errors.append(f"Beklenen confirm: false, Alinan: {result.get('confirm')}")

    if errors:
        print(f"\n[WARN] Uyarilar ({len(errors)}):")
        for e in errors:
            print(f"   - {e}")
    else:
        print("\n[PASS] TUM DOGRULAMALAR BASARILI!")
        print("   + action  = open_app")
        print("   + app     = spotify")
        print("   + confirm = false")

    print(f"\n{'=' * 60}")
    print(f"  Test tamamlandi.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
