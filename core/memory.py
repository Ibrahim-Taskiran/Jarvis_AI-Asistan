"""
core/memory.py - JARVIS Hafıza Yöneticisi
Kullanıcı komutlarını SQLite veritabanına kaydeder ve geçmişi yönetir.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """Komut geçmişini ve bağlamı veritabanında saklayan sınıf."""

    def __init__(self, db_path="C:/Users/ibrah/Documents/GitHub/Jarvis/data/memory.db"):
        self.db_path = Path(db_path)
        # Data klasörünün var olduğundan emin ol
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self):
        """Yeni bir veritabanı bağlantısı döndürür."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Veritabanı tablosunu yoksa oluşturur."""
        query = '''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            raw_text TEXT,
            action TEXT,
            params TEXT,
            result TEXT,
            model_used TEXT,
            response_time REAL
        )
        '''
        try:
            with self._get_conn() as conn:
                conn.execute(query)
        except Exception as e:
            logger.error(f"Veritabanı başlatılırken hata: {e}")

    def save_command(self, raw_text: str, action: str, params: dict, result: str, model_used: str, response_time: float):
        """Çalıştırılan komutu veritabanına kaydeder."""
        query = '''
        INSERT INTO commands (timestamp, raw_text, action, params, result, model_used, response_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params_str = json.dumps(params, ensure_ascii=False) if params else "{}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with self._get_conn() as conn:
                conn.execute(query, (timestamp, raw_text, action, params_str, result, model_used, response_time))
            logger.debug(f"Komut kaydedildi: {action}")
        except Exception as e:
            logger.error(f"Komut kaydedilirken hata: {e}")

    def get_last_command(self) -> dict | None:
        """En son çalıştırılan komutu getirir."""
        query = "SELECT * FROM commands ORDER BY id DESC LIMIT 1"
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(query).fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Son komut alınırken hata: {e}")
        return None

    def get_history(self, limit: int = 10) -> list[dict]:
        """Geçmiş komutları liste halinde getirir."""
        query = "SELECT * FROM commands ORDER BY id DESC LIMIT ?"
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(query, (limit,)).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Geçmiş alınırken hata: {e}")
            return []

    def clear_history(self):
        """Tüm komut geçmişini temizler."""
        query = "DELETE FROM commands"
        try:
            with self._get_conn() as conn:
                conn.execute(query)
            logger.info("Komut geçmişi temizlendi.")
        except Exception as e:
            logger.error(f"Geçmiş temizlenirken hata: {e}")
            raise e

    def get_last_opened_app(self) -> str | None:
        """En son açılan uygulamayı bulur."""
        query = "SELECT params FROM commands WHERE action = 'open_app' ORDER BY id DESC LIMIT 1"
        try:
            with self._get_conn() as conn:
                row = conn.execute(query).fetchone()
                if row and row[0]:
                    params = json.loads(row[0])
                    return params.get("app")
        except Exception as e:
            logger.error(f"Son açılan uygulama bulunurken hata: {e}")
        return None
