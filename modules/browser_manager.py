"""
modules/browser_manager.py - Tarayıcı Yöneticisi
Web sitelerini ve URL'leri istenen tarayıcı ile açar.
"""

import webbrowser
import logging

logger = logging.getLogger(__name__)

class BrowserManager:
    """Tarayıcı ve web sitelerini açma işlemlerini yönetir."""
    
    SITE_MAP = {
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "okul": "https://obs.firat.edu.tr",
        "google": "https://www.google.com",
        "chatgpt": "https://chat.openai.com"
    }

    def open_url(self, url: str, browser: str = "default") -> dict:
        """Belirtilen URL'yi açar."""
        try:
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
                
            if browser != "default":
                try:
                    webbrowser.get(browser).open(url)
                except webbrowser.Error:
                    logger.warning(f"Belirtilen tarayıcı ({browser}) bulunamadı, varsayılan kullanılıyor.")
                    webbrowser.open(url)
            else:
                webbrowser.open(url)
                
            return {"success": True, "message": f"{url} adresi başarıyla açıldı."}
        except Exception as e:
            logger.error(f"URL açılırken hata: {e}")
            return {"success": False, "message": f"URL açılamadı: {e}"}

    def open_site(self, site_name: str) -> dict:
        """Yaygın site isimlerini URL'ye eşleştirerek açar."""
        site_name_lower = site_name.lower().strip()
        
        # Site eşleştirme kontrolü
        for key, url in self.SITE_MAP.items():
            if key in site_name_lower or site_name_lower in key:
                return self.open_url(url)
                
        # Eşleşme yoksa doğrudan url olarak girmeyi dene
        return self.open_url(site_name_lower)
