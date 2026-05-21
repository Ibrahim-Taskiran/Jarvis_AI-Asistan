import sys
import os
import time

class MockTTS:
    def speak(self, text):
        print(f"[TTS] Sesli okunan: '{text}'")

class MockListener:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def listen(self):
        time.sleep(1) # Gerçek listener'ın bloklama süresini simüle et
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            print(f"[Listener] Algılanan ses: '{resp}'")
            return resp
        print("[Listener] Algılanan ses: ''")
        return ""

def main():
    from core.safety import SafetyGuard
    guard = SafetyGuard()
    tts = MockTTS()
    
    print("\n--- TEST 1: 'evet' YANITI ---")
    listener_evet = MockListener(["anlaşılmayan ses", "evet yapalım"])
    res = guard.ask_confirm("shutdown", tts, listener_evet)
    print(f"-> Sonuç (Beklenen: True): {res}\n")

    print("--- TEST 2: 'hayır' YANITI ---")
    listener_hayir = MockListener(["hayır istemiyorum"])
    res = guard.ask_confirm("delete_file", tts, listener_hayir)
    print(f"-> Sonuç (Beklenen: False): {res}\n")

    print("--- TEST 3: ZAMAN AŞIMI ---")
    # Hep boş dönerse 5sn sonra time out olmalı
    listener_timeout = MockListener(["", "", "", "", "", ""])
    res = guard.ask_confirm("restart", tts, listener_timeout)
    print(f"-> Sonuç (Beklenen: False): {res}\n")

    print("--- TEST 4: GÜVENLİ İŞLEM (ONAY GEREKMEZ) ---")
    listener_safe = MockListener([])
    res = guard.ask_confirm("open_app", tts, listener_safe)
    print(f"-> Sonuç (Beklenen: True): {res}\n")

if __name__ == "__main__":
    main()
