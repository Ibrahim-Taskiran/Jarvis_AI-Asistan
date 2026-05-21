"""
modules/daily_summary.py - Günlük Özet Modülü
Kullanıcının projelerinin Git durumunu ve gün içindeki asistan komut istatistiklerini özetler.
"""

import datetime
import logging
from pathlib import Path
from config import DEFAULT_GIT_PATH
from modules.git_manager import GitManager
from core.memory import MemoryManager

logger = logging.getLogger(__name__)

class DailySummary:
    """Kullanıcının günlük komut geçmişini ve proje durumlarını özetler."""
    
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory = memory_manager or MemoryManager()
        self.base_path = Path(DEFAULT_GIT_PATH)
        
    def _get_todays_command_count(self) -> int:
        """Bugün çalıştırılan komut sayısını veritabanından çeker."""
        today = datetime.date.today().isoformat()
        query = "SELECT COUNT(*) FROM commands WHERE timestamp LIKE ?"
        try:
            with self.memory._get_conn() as conn:
                count = conn.execute(query, (f"{today}%",)).fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Komut sayısı alınırken hata: {e}")
            return 0

    def generate_summary(self) -> str:
        """Tüm projeleri tarayarak günlük özeti metin olarak üretir."""
        count = self._get_todays_command_count()
        summary_parts = [f"Günaydın! Bugün {count} komut verdin."]
        
        if not self.base_path.exists():
            summary_parts.append("Projeler dizini bulunamadı.")
            return " ".join(summary_parts)
            
        repo_summaries = []
        
        # Sadece 1. seviye alt klasörlere bak (.git olanları seç)
        for item in self.base_path.iterdir():
            if item.is_dir() and (item / ".git").exists():
                git_mgr = GitManager(repo_path=str(item))
                repo = git_mgr.repo
                if repo:
                    try:
                        # Son commit mesajını al
                        last_commit = repo.head.commit
                        commit_msg = last_commit.message.split('\n')[0].strip()
                        
                        # Git durumunu kontrol et
                        status = git_mgr.git_status()
                        changes = status.get("changes", 0)
                        
                        changes_text = f"{changes} değiştirilmiş dosya var" if changes > 0 else "değiştirilmemiş dosya var"
                        
                        repo_summaries.append(
                            f"{item.name} projesinde son commit: '{commit_msg}'. {item.name} projesinde {changes_text}."
                        )
                    except Exception as e:
                        logger.warning(f"Proje özeti alınamadı ({item.name}): {e}")
        
        if repo_summaries:
            summary_parts.append(" ".join(repo_summaries))
            
        return " ".join(summary_parts)

    def speak_summary(self, tts):
        """Özeti üretir ve sesli okur."""
        summary = self.generate_summary()
        logger.info(f"Günlük Özet Okunuyor: {summary}")
        tts.speak(summary)
