import sys
import time

def main():
    from modules.app_manager import AppManager
    manager = AppManager()
    
    print("\n--- TEST 1: open_app('spotify') ---")
    res1 = manager.open_app("spotify")
    print(res1)
    
    print("\n--- TEST 2: open_app('spot') (fuzzy) ---")
    # Zaten açıksa bile sonuç başarılı dönecektir.
    res2 = manager.open_app("spot")
    print(res2)

    print("\n--- TEST 3: open_app('minecraft') (not in config) ---")
    res3 = manager.open_app("minecraft")
    print(res3)

    # Kapatmadan önce açılması için biraz süre tanı
    print("\n[INFO] Uygulamanın tam başlatılması için 3 saniye bekleniyor...")
    time.sleep(3)

    print("\n--- TEST 4: close_app('spotify') ---")
    res4 = manager.close_app("spotify")
    print(res4)

if __name__ == "__main__":
    main()
