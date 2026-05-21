import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.window import JarvisWindow

def main():
    app = QApplication(sys.argv)
    window = JarvisWindow()
    window.show()
    
    # Adım adım arayüz güncellemelerini simüle et
    def step1():
        print("[TEST] Adım 1: İşleniyor...")
        window.set_status("İşleniyor...")
        window.set_last_command("Projeyi GitHub'a yükle")

    def step2():
        print("[TEST] Adım 2: Tamamlandı.")
        window.set_status("Tamamlandı")
        window.set_result("Push işlemi başarıyla tamamlandı.", success=True)
        window.set_model_info("Mistral 7B", 3.2)

    def step3():
        print("[TEST] Adım 3: Hata senaryosu.")
        window.set_status("Hata")
        window.set_last_command("Silinemeyecek dosya")
        window.set_result("Dosya bulunamadı veya erişim reddedildi.", success=False)
        window.set_model_info("Llama 3B", 0.9)

    def step4():
        print("[TEST] Adım 4: Uyku Modu ve Çıkış.")
        window.set_status("Uyku Modunda")
        QTimer.singleShot(1500, app.quit) # 1.5 saniye sonra kapat

    # Zamanlayıcıları kur
    QTimer.singleShot(1500, step1)
    QTimer.singleShot(3500, step2)
    QTimer.singleShot(5500, step3)
    QTimer.singleShot(7500, step4)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
