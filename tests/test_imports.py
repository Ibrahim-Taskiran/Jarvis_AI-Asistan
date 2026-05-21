import sys
from PyQt6.QtWidgets import QApplication

def test_dry_run():
    print("[TEST] main.py import ediliyor...")
    try:
        import main
        print("[TEST] Tüm modüller başarıyla import edildi.")
        
        # Sınıfları başlatmayı test et (QApplication objesi gerekli)
        app = QApplication(sys.argv)
        
        print("[TEST] JarvisWindow başlatılıyor...")
        window = main.JarvisWindow()
        
        print("[TEST] JarvisApp başlatılıyor (Çekirdek Modüller Yükleniyor)...")
        jarvis = main.JarvisApp(window)
        
        print("[TEST] Sınıflar hatasız şekilde başlatıldı!")
        print("[TEST] Dry-run başarıyla tamamlandı.")
        
    except Exception as e:
        print(f"[TEST] Hata ile karşılaşıldı: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dry_run()
