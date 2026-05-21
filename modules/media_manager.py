"""
modules/media_manager.py - Medya Yöneticisi
Klavye kısayolları ile medya kontrollerini (Spotify vb.) yönetir.
"""

import pyautogui
import logging

logger = logging.getLogger(__name__)

class MediaManager:
    """Klavye kısayolları (pyautogui) ile medya oynatım işlemlerini yönetir."""
    
    def play_pause(self) -> dict:
        try:
            pyautogui.press('space')
            return {"success": True, "message": "Oynat/Duraklat işlemi yapıldı."}
        except Exception as e:
            logger.error(f"Medya hatası (play_pause): {e}")
            return {"success": False, "message": "Medya işlemi başarısız oldu."}
            
    def next_track(self) -> dict:
        try:
            pyautogui.hotkey('ctrl', 'right')
            return {"success": True, "message": "Sonraki parçaya geçildi."}
        except Exception as e:
            logger.error(f"Medya hatası (next_track): {e}")
            return {"success": False, "message": "Sonraki parçaya geçilemedi."}
            
    def prev_track(self) -> dict:
        try:
            pyautogui.hotkey('ctrl', 'left')
            return {"success": True, "message": "Önceki parçaya geçildi."}
        except Exception as e:
            logger.error(f"Medya hatası (prev_track): {e}")
            return {"success": False, "message": "Önceki parçaya geçilemedi."}
            
    def volume_up(self) -> dict:
        try:
            pyautogui.hotkey('ctrl', 'up')
            return {"success": True, "message": "Ses açıldı."}
        except Exception as e:
            logger.error(f"Medya hatası (volume_up): {e}")
            return {"success": False, "message": "Ses açılamadı."}
            
    def volume_down(self) -> dict:
        try:
            pyautogui.hotkey('ctrl', 'down')
            return {"success": True, "message": "Ses kısıldı."}
        except Exception as e:
            logger.error(f"Medya hatası (volume_down): {e}")
            return {"success": False, "message": "Ses kısılamadı."}

    def media_control(self, action: str) -> dict:
        """Gelen eylem metnine (action) göre doğru metodu çağırır."""
        action = action.lower()
        if any(word in action for word in ["play", "pause", "dur", "başlat", "oynat"]):
            return self.play_pause()
        elif any(word in action for word in ["next", "sonraki", "geç"]):
            return self.next_track()
        elif any(word in action for word in ["prev", "önceki", "geri"]):
            return self.prev_track()
        elif any(word in action for word in ["up", "aç", "arttır", "yükselt"]):
            return self.volume_up()
        elif any(word in action for word in ["down", "kıs", "azalt", "düşür"]):
            return self.volume_down()
        else:
            return {"success": False, "message": "Anlaşılmayan medya komutu."}
