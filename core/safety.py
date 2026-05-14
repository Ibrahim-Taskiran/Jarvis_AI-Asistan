"""
core/safety.py - JARVIS Güvenlik Modülü
Tehlikeli komutlar için onay mekanizması.
"""

import time
import logging

logger = logging.getLogger(__name__)

DANGEROUS_ACTIONS = ["shutdown", "restart", "delete_file", "organize_files", "git_force_push"]

class SafetyGuard:
    """Tehlikeli işlemler için onay yönetim sınıfı."""

    def requires_confirm(self, action: str) -> bool:
        """İşlemin onay gerektirip gerektirmediğini kontrol eder."""
        return action in DANGEROUS_ACTIONS

    def ask_confirm(self, action: str, tts, listener) -> bool:
        """
        Kullanıcıdan sesli onay ister.
        Maksimum 5 saniye bekler.
        "evet" denirse True, "hayır" denirse veya süre dolarsa False döner.
        """
        if not self.requires_confirm(action):
            return True

        logger.info(f"Onay bekleniyor: {action}")
        tts.speak("Bu işlemi yapmak istediğinden emin misin?")
        
        start_time = time.time()
        
        # 5 saniye boyunca dinle
        while time.time() - start_time < 5.0:
            logger.debug("Onay için dinleniyor...")
            text = listener.listen().lower()
            
            if not text:
                continue
                
            logger.debug(f"Onay algılanan metin: {text}")
            
            if "evet" in text:
                logger.info(f"İşlem ({action}) onaylandı.")
                return True
            elif "hayır" in text or "hayir" in text:
                logger.info(f"İşlem ({action}) reddedildi.")
                return False
                
        logger.warning(f"Onay zaman aşımına uğradı ({action}).")
        return False
