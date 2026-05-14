"""
modules/app_manager.py - Uygulama Yöneticisi
Uygulamaları açma ve kapatma işlemlerini gerçekleştirir.
"""

import os
import logging
import subprocess
import psutil
from config import APPS

logger = logging.getLogger(__name__)

class AppManager:
    """Uygulama açma ve kapatma işlemlerini yönetir."""
    
    def _find_app_key(self, app_name: str) -> str | None:
        """Kullanıcının söylediği isimle config'deki APPS anahtarlarını fuzzy eşleştirir."""
        app_name = app_name.lower().strip()
        
        # Tam eşleşme
        if app_name in APPS:
            return app_name
            
        # Kısmi eşleşme
        for key in APPS:
            if app_name in key or key in app_name:
                return key
                
        return None

    def open_app(self, app_name: str) -> dict:
        """Uygulamayı başlatır."""
        key = self._find_app_key(app_name)
        if not key:
            return {"success": False, "message": f"Uygulama bulunamadı: {app_name}"}
            
        app_path = APPS[key]
        
        if not os.path.exists(app_path):
            return {"success": False, "message": f"{key} uygulaması belirtilen yolda bulunamadı."}
            
        try:
            subprocess.Popen([app_path], creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
            logger.info(f"Uygulama açıldı: {key}")
            return {"success": True, "message": f"{key} açıldı."}
        except Exception as e:
            logger.error(f"{key} açılırken hata oluştu: {e}")
            return {"success": False, "message": f"{key} açılamadı."}

    def close_app(self, app_name: str) -> dict:
        """Çalışan uygulamayı bulup sonlandırır."""
        key = self._find_app_key(app_name)
        if not key:
            return {"success": False, "message": f"Uygulama bulunamadı: {app_name}"}
            
        app_path = APPS[key]
        executable_name = os.path.basename(app_path).lower()
        
        killed = False
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == executable_name:
                        proc.kill()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if killed:
                logger.info(f"Uygulama kapatıldı: {key}")
                return {"success": True, "message": f"{key} kapatıldı."}
            else:
                logger.info(f"Uygulama çalışanlar arasında bulunamadı: {key}")
                return {"success": False, "message": f"{key} çalışan işlemler arasında bulunamadı."}
                
        except Exception as e:
            logger.error(f"{key} kapatılırken hata: {e}")
            return {"success": False, "message": f"{key} kapatılamadı."}
