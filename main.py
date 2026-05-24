"""
main.py - JARVIS Ana Başlatıcı
Tüm çekirdek ve modülleri birbirine bağlayan, arayüzü başlatan giriş noktası.
"""

import sys
import json
import time
import threading
import logging
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, QPoint

# Konfigürasyon
from config import SLEEP_TIMEOUT_MINUTES, TEXT_MODE

# Çekirdek (Core)
from core.listener import Listener
from core.brain import Brain
from core import router
from core.memory import MemoryManager
from core.context import ContextManager
from core.tts import TTS
from core.safety import SafetyGuard

# Modüller (Modules)
from modules.app_manager import AppManager
from modules.git_manager import GitManager
from modules.terminal_manager import TerminalManager
from modules.file_manager import FileManager
from modules.browser_manager import BrowserManager
from modules.media_manager import MediaManager
from modules.daily_summary import DailySummary
from modules.prompt_generator import PromptGenerator
from modules import free_chat
from modules.gesture_manager import GestureManager

# Arayüz (UI)
from ui.window import JarvisWindow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JarvisApp(QObject):
    """JARVIS uygulamasının iş mantığını ve arayüz entegrasyonunu yönetir."""
    
    # Thread'ler arası arayüzü güvenle güncellemek için PyQt Sinyalleri
    sig_status = pyqtSignal(str)
    sig_command = pyqtSignal(str)
    sig_result = pyqtSignal(str, bool)
    sig_model_info = pyqtSignal(str, float)
    sig_camera_state = pyqtSignal(bool)

    def __init__(self, window: JarvisWindow):
        super().__init__()
        self.window = window
        
        # Sinyalleri arayüz metotlarına bağla
        self.sig_status.connect(self.window.set_status)
        self.sig_command.connect(self.window.set_last_command)
        self.sig_result.connect(self.window.set_result)
        self.sig_model_info.connect(self.window.set_model_info)
        self.sig_camera_state.connect(self.update_camera_ui)

        # Arayüz Etkileşimlerini Bağla
        self.window.input_command.returnPressed.connect(self.handle_text_submit)
        self.window.btn_send.clicked.connect(self.handle_text_submit)
        self.window.btn_mic.clicked.connect(self.handle_mic_toggle)
        self.window.btn_camera.clicked.connect(self.handle_camera_toggle)
        self.window.btn_stop.clicked.connect(self.handle_stop_playback)
        self.window.btn_settings.clicked.connect(self.handle_settings_click)
        self.window.sig_sleep_requested.connect(self.trigger_sleep_mode)
        self.window.sig_clear_mem_requested.connect(self.clear_memory)

        # Modüllerin başlatılması
        logger.info("Çekirdek sistemler yükleniyor...")
        self.memory = MemoryManager()
        self.context = ContextManager(self.memory)
        self.tts = TTS()
        self.safety = SafetyGuard()
        
        # Hata fırlatabilecek bağımlılıklar
        self.listener = Listener()
        self.brain = Brain()
        
        logger.info("Eylem modülleri yükleniyor...")
        self.app_manager = AppManager()
        self.terminal_manager = TerminalManager()
        self.file_manager = FileManager()
        self.browser_manager = BrowserManager()
        self.media_manager = MediaManager()
        self.daily_summary = DailySummary(self.memory)
        self.prompt_generator = PromptGenerator()
        self.gesture_manager = GestureManager()

        # Uyku modu zamanlayıcısı
        self.last_command_time = time.time()
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.check_sleep_mode)
        self.sleep_timer.start(60000) # Her 1 dakikada bir kontrol et

    def startup_sequence(self):
        """Asistanın başlangıç rutini (Ayrı thread'de UI bloklanmadan çalışır)."""
        try:
            self.sig_status.emit("Başlatılıyor...")
            self.tts.speak("JARVIS başlatılıyor.")
            
            # Günlük özet (devre dışı)
            # self.daily_summary.speak_summary(self.tts)
            
            # Dinleme modunu başlat
            self.sig_status.emit("Dinleniyor...")
            if TEXT_MODE:
                self._start_text_input_loop()
            else:
                self.listener.start_listening(self.on_command, tts=self.tts)
        except Exception as e:
            logger.error(f"Başlatma rutini hatası: {e}")
            self.sig_status.emit("Hata")
            self.sig_result.emit(f"Başlatma hatası: {e}", False)

    def _start_text_input_loop(self):
        """Konsol üzerinden metin girişi ile komut alma döngüsü (TEXT_MODE için)."""
        def _text_loop():
            logger.info("TEXT_MODE aktif: Konsol metin girişi bekleniyor...")
            print("\n" + "=" * 50)
            print("  JARVIS - Metin Giriş Modu")
            print("  Çıkmak için 'çık' veya 'exit' yazın.")
            print("=" * 50 + "\n")
            while True:
                try:
                    text = input("Komut: ").strip()
                    if not text:
                        continue
                    if text.lower() in ("çık", "exit", "quit", "q"):
                        print("JARVIS kapatılıyor...")
                        logger.info("TEXT_MODE: Kullanıcı çıkış yaptı.")
                        os._exit(0)
                    self.on_command(text)
                except (EOFError, KeyboardInterrupt):
                    print("\nJARVIS kapatılıyor...")
                    os._exit(0)

        threading.Thread(target=_text_loop, daemon=True).start()

    def check_sleep_mode(self):
        """Belirlenen süre boyunca komut gelmezse uyku moduna geçer."""
        if self.listener.is_paused:
            return
            
        elapsed = time.time() - self.last_command_time
        if elapsed > (SLEEP_TIMEOUT_MINUTES * 60):
            logger.info("Uyku moduna geçiliyor...")
            self.listener.pause()
            self.sig_status.emit("Uyku Modunda")
            self.tts.speak("Uzun süre işlem yapılmadı. Uyku moduna geçiyorum.")

    def execute_action(self, action: str, params: dict) -> dict:
        """JSON ile tespit edilen eylemi doğru modüle yönlendirir."""
        app = params.get("app", "")
        repo = params.get("repo", "")
        cmd = params.get("command", "")
        url = params.get("url", "")
        path = params.get("path", "")
        media_act = params.get("action", "")

        # Uygulama Yöneticisi
        if action == "open_app": return self.app_manager.open_app(app)
        if action == "close_app": return self.app_manager.close_app(app)
        
        # Sistem
        if action == "shutdown":
            os.system("shutdown /s /t 60")
            return {"success": True, "message": "Bilgisayar 60 saniye içinde kapatılacak."}
        if action == "restart":
            os.system("shutdown /r /t 60")
            return {"success": True, "message": "Bilgisayar 60 saniye içinde yeniden başlatılacak."}
            
        # Git Yöneticisi
        if action == "git_push": return GitManager(repo).git_push(params.get("message"))
        if action == "git_pull": return GitManager(repo).git_pull()
        if action == "git_status": return GitManager(repo).git_status()
        if action == "git_fetch": return GitManager(repo).git_fetch()
        
        # Terminal Yöneticisi
        if action == "run_terminal": return self.terminal_manager.run_command(cmd)
        
        # Tarayıcı Yöneticisi
        if action == "open_browser":
            if "http" in url or "." in url:
                return self.browser_manager.open_url(url)
            else:
                return self.browser_manager.open_site(url)
                
        # Medya Yöneticisi
        if action == "media_control": return self.media_manager.media_control(media_act)
        if action == "volume_control": return self.media_manager.media_control(media_act or "ses")
        
        # Dosya Yöneticisi
        if action == "organize_files": return self.file_manager.organize_desktop()
        if action == "summarize_file": return self.file_manager.summarize_file(path)
        if action == "create_readme": return self.file_manager.create_readme(repo)
        
        # Prompt / Günlük Özet
        if action == "generate_prompt": return self.prompt_generator.generate_project_prompt(path or repo)
        if action == "daily_summary":
            return {"success": True, "message": self.daily_summary.generate_summary()}
            
        # Jest / Kamera Yöneticisi
        if action == "camera_on":
            res = self.gesture_manager.start()
            if res.get("success"):
                self.sig_camera_state.emit(True)
            return res
        if action == "camera_off":
            res = self.gesture_manager.stop()
            if res.get("success"):
                self.sig_camera_state.emit(False)
            return res

        return {"success": False, "message": f"Desteklenmeyen eylem: {action}"}

    def on_command(self, text: str):
        """Kullanıcının söylediği her cümlede tetiklenir."""
        if not text.strip():
            return
            
        self.last_command_time = time.time()
        
        # Uyku modundan uyandırma kontrolü
        if self.listener.is_paused:
            if "jarvis" in text.lower() or "uyan" in text.lower():
                self.listener.resume()
                self.sig_status.emit("Dinleniyor...")
                self.tts.speak("Sizi dinliyorum.")
            return

        self.sig_status.emit("İşleniyor...")
        self.sig_command.emit(text)
        
        try:
            start_time = time.time()
            ctx = self.context.get_context_summary()
            
            # Brain (Ollama) üzerinden komutu anlamlandır
            response = self.brain.think(text, context=ctx)
            
            # Ollama yanıtı zaten dict olabilir, kontrol et
            if isinstance(response, dict):
                parsed = response
            elif isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = json.loads(str(response))
            
            action = parsed.get("action", "unknown")
            params = parsed.get("params", {})
            
            # Router üzerinden hangi LLM modelinin seçildiğini al
            route_info = router.route(action)
            model_used = route_info.get("model", "unknown")
            module_name = route_info.get("module", "unknown")
            
            # free_chat modülüne yönlendirilmişse ham metni gönder
            if module_name == "free_chat":
                logger.info(f"Free chat modülüne yönlendiriliyor: '{text}'")
                result_dict = free_chat.execute(text)
            else:
                # Tehlikeli işlemse onay sor
                if self.safety.requires_confirm(action):
                    self.sig_status.emit("Onay Bekleniyor...")
                    if not self.safety.ask_confirm(action, self.tts, self.listener):
                        raise Exception("İşlem kullanıcı tarafından reddedildi veya zaman aşımına uğradı.")
                
                # Komutu modülde çalıştır
                result_dict = self.execute_action(action, params)
            resp_time = time.time() - start_time
            
            self.sig_model_info.emit(model_used, resp_time)
            
            # Hafızaya logla
            self.memory.save_command(
                raw_text=text,
                action=action,
                params=params,
                result=result_dict.get("message", ""),
                model_used=model_used,
                response_time=resp_time
            )
            
            # Sonucu UI'a yansıt ve sesli oku
            if result_dict.get("success"):
                self.sig_result.emit(result_dict.get("message", "Tamamlandı."), True)
                self.sig_status.emit("Konuşuyor...")
                self.tts.speak(result_dict.get("message", "İşlem tamamlandı."))
            else:
                self.sig_result.emit(result_dict.get("message", "Hata oluştu."), False)
                self.sig_status.emit("Konuşuyor...")
                self.tts.speak(result_dict.get("message", "İşlem sırasında hata oluştu."))
                
        except Exception as e:
            logger.error(f"Komut akışı hatası: {e}")
            self.sig_result.emit(str(e), False)
            self.sig_status.emit("Konuşuyor...")
            self.tts.speak("Üzgünüm, komutu işlerken bir sorun oluştu.")
            
        finally:
            if not self.listener.is_paused:
                self.sig_status.emit("Dinleniyor...")
            else:
                self.sig_status.emit("Uykuda")

    def handle_text_submit(self):
        """Kullanıcının metin olarak girdiği komutu kuyruğa ekler ve arka planda çalıştırır."""
        text = self.window.input_command.text().strip()
        if not text:
            return
        self.window.input_command.clear()
        
        # UI kilitlenmesini önlemek için arka planda çalıştır
        threading.Thread(target=self.on_command, args=(text,), daemon=True).start()

    def handle_mic_toggle(self):
        """Mikrofonu arayüz üzerinden kapatıp açar ve stilini günceller."""
        if self.listener.is_paused:
            self.listener.resume()
            self.sig_status.emit("Dinleniyor...")
            self.window.btn_mic.setText("🎙️ Mikrofon açık")
            self.window.btn_mic.setStyleSheet(
                "QPushButton {"
                "    background-color: #0f1917;"
                "    border: 1px solid #133c30;"
                "    border-radius: 8px;"
                "    color: #00ff88;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    background-color: #132e26;"
                "    border: 1px solid #00ff88;"
                "}"
            )
        else:
            self.listener.pause()
            self.sig_status.emit("Uykuda")
            self.window.btn_mic.setText("🎙️ Mikrofon kapalı")
            self.window.btn_mic.setStyleSheet(
                "QPushButton {"
                "    background-color: #12151c;"
                "    border: 1px solid #202633;"
                "    border-radius: 8px;"
                "    color: #5c6b73;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    border: 1px solid #5c6b73;"
                "}"
            )

    def handle_camera_toggle(self):
        """Kamerayı arayüz üzerinden kapatıp açar."""
        if self.gesture_manager.is_running:
            self.gesture_manager.stop()
            self.sig_camera_state.emit(False)
            self.sig_result.emit("Kamera kapatıldı.", True)
            self.tts.speak_async("Kamera kapatıldı.")
        else:
            self.gesture_manager.start()
            self.sig_camera_state.emit(True)
            self.sig_result.emit("Kamera açıldı.", True)
            self.tts.speak_async("Kamera açıldı.")

    def update_camera_ui(self, active: bool):
        """Kamera butonunun stilini thread-safe şekilde günceller."""
        if active:
            self.window.btn_camera.setText("📷 Kamera açık")
            self.window.btn_camera.setStyleSheet(
                "QPushButton {"
                "    background-color: #0f1917;"
                "    border: 1px solid #133c30;"
                "    border-radius: 8px;"
                "    color: #00ff88;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    background-color: #132e26;"
                "    border: 1px solid #00ff88;"
                "}"
            )
        else:
            self.window.btn_camera.setText("📷 Kamera kapalı")
            self.window.btn_camera.setStyleSheet(
                "QPushButton {"
                "    background-color: #1a1114;"
                "    border: 1px solid #3c131a;"
                "    border-radius: 8px;"
                "    color: #ff3333;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    background-color: #2e1318;"
                "    border: 1px solid #ff3333;"
                "}"
            )

    def handle_stop_playback(self):
        """Çalınan sesi veya çalışan okuma işlemini hemen durdurur."""
        self.tts.stop()
        if self.listener.is_paused:
            self.sig_status.emit("Uykuda")
        else:
            self.sig_status.emit("Dinleniyor...")

    def handle_settings_click(self):
        """Seçenekler butonuna tıklandığında HUD menüsünü açar."""
        btn = self.window.btn_settings
        pos = btn.mapToGlobal(QPoint(0, 0))
        # Butonun hemen sol/üst tarafında aç
        self.window.show_settings_menu(QPoint(pos.x() - 100, pos.y() - 100))

    def trigger_sleep_mode(self):
        """Arayüz üzerinden manuel uyku modunu kapatıp açar (Toggle)."""
        if self.listener.is_paused:
            # Uykudan uyandır
            self.listener.resume()
            self.sig_status.emit("Dinleniyor...")
            self.window.btn_mic.setText("🎙️ Mikrofon açık")
            self.window.btn_mic.setStyleSheet(
                "QPushButton {"
                "    background-color: #0f1917;"
                "    border: 1px solid #133c30;"
                "    border-radius: 8px;"
                "    color: #00ff88;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    background-color: #132e26;"
                "    border: 1px solid #00ff88;"
                "}"
            )
            self.tts.speak_async("Sizi dinliyorum.")
        else:
            # Uykuya al
            self.listener.pause()
            self.sig_status.emit("Uykuda")
            self.window.btn_mic.setText("🎙️ Mikrofon kapalı")
            self.window.btn_mic.setStyleSheet(
                "QPushButton {"
                "    background-color: #12151c;"
                "    border: 1px solid #202633;"
                "    border-radius: 8px;"
                "    color: #5c6b73;"
                "    font-size: 11px;"
                "    font-weight: bold;"
                "    min-height: 34px;"
                "    padding: 0 15px;"
                "}"
                "QPushButton:hover {"
                "    border: 1px solid #5c6b73;"
                "}"
            )
            self.tts.speak_async("Uyku moduna geçiliyor.")

    def clear_memory(self):
        """Hafıza verilerini siler."""
        try:
            self.memory.clear_history()
            self.sig_result.emit("Komut hafızası başarıyla temizlendi.", True)
            self.tts.speak_async("Hafıza temizlendi.")
        except Exception as e:
            logger.error(f"Hafıza temizlenemedi: {e}")
            self.sig_result.emit("Hafıza temizlenemedi.", False)


def main():
    app = QApplication(sys.argv)
    window = JarvisWindow()
    
    jarvis = JarvisApp(window)
    
    # Startup rutinini UI'ı kilitlemeden arka planda başlat
    threading.Thread(target=jarvis.startup_sequence, daemon=True).start()
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
