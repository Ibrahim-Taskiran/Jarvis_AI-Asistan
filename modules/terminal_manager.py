"""
modules/terminal_manager.py - Terminal Yöneticisi
Shell komutlarını ve sanal ortam işlemlerini gerçekleştirir.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

class TerminalManager:
    """Sistem komutları, sanal ortam ve pip işlemlerini yönetir."""
    
    def run_command(self, cmd: str) -> dict:
        """Shell komutu çalıştırır ve çıktıyı döndürür."""
        try:
            # shell=True ile komut çalıştırılır
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    "success": True, 
                    "message": "Komut başarıyla çalıştırıldı.", 
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False, 
                    "message": f"Komut hatayla sonuçlandı. Hata Kodu: {result.returncode}", 
                    "error": result.stderr.strip()
                }
        except Exception as e:
            logger.error(f"Komut çalıştırma hatası: {e}")
            return {"success": False, "message": f"Komut çalıştırılamadı: {e}"}

    def update_pip(self) -> dict:
        """Pip paket yöneticisini günceller."""
        cmd = "python -m pip install --upgrade pip"
        res = self.run_command(cmd)
        if res["success"]:
            return {"success": True, "message": "Pip başarıyla güncellendi."}
        else:
            return {"success": False, "message": "Pip güncellenirken hata oluştu."}

    def create_venv(self, name: str = "venv") -> dict:
        """Sanal ortam (virtual environment) oluşturur."""
        cmd = f"python -m venv {name}"
        res = self.run_command(cmd)
        if res["success"]:
            return {"success": True, "message": f"'{name}' adında sanal ortam başarıyla oluşturuldu."}
        else:
            return {"success": False, "message": "Sanal ortam oluşturulamadı."}

    def create_requirements(self) -> dict:
        """Sistemdeki paketleri listeleyerek requirements.txt dosyası oluşturur."""
        cmd = "pip freeze > requirements.txt"
        res = self.run_command(cmd)
        if res["success"]:
            return {"success": True, "message": "requirements.txt dosyası başarıyla oluşturuldu/güncellendi."}
        else:
            return {"success": False, "message": "requirements.txt oluşturulurken hata yaşandı."}
