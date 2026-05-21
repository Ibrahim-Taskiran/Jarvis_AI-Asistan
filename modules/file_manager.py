"""
modules/file_manager.py - Dosya Yöneticisi
Masaüstü düzenleme, dosya özeti çıkarma, README oluşturma ve indirme temizliği gibi dosya operasyonlarını yürütür.
"""

import os
import time
import shutil
import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileManager:
    """Dosya ve dizin işlemlerini yöneten sınıf."""

    EXT_MAP = {
        ".pdf": "Belgeler", ".docx": "Belgeler", ".txt": "Belgeler", ".doc": "Belgeler",
        ".jpg": "Resimler", ".jpeg": "Resimler", ".png": "Resimler", ".gif": "Resimler",
        ".mp4": "Videolar", ".mkv": "Videolar", ".avi": "Videolar",
        ".mp3": "Müzik", ".wav": "Müzik",
        ".zip": "Arşivler", ".rar": "Arşivler", ".7z": "Arşivler", ".tar": "Arşivler", ".gz": "Arşivler"
    }

    def __init__(self, username: str = "ibrah"):
        # Varsayılan kullanıcı yolları
        self.desktop_path = Path(f"C:/Users/{username}/Desktop")
        self.downloads_path = Path(f"C:/Users/{username}/Downloads")

    def organize_desktop(self, dry_run: bool = False) -> dict:
        """Masaüstündeki dosyaları uzantılarına göre alt klasörlere ayırır."""
        if not self.desktop_path.exists():
            return {"success": False, "message": f"Masaüstü dizini bulunamadı: {self.desktop_path}"}
            
        summary = {"Belgeler": 0, "Resimler": 0, "Videolar": 0, "Müzik": 0, "Arşivler": 0, "Diğer": 0}
        moved_files = []

        for item in self.desktop_path.iterdir():
            # Yalnızca dosyaları al (Gizli dosyalar, .ini veya .lnk kısayollarını hariç tut)
            if item.is_file() and not item.name.startswith(".") and item.name.lower() != "desktop.ini" and not item.name.lower().endswith(".lnk"):
                ext = item.suffix.lower()
                folder_name = self.EXT_MAP.get(ext, "Diğer")
                
                target_folder = self.desktop_path / folder_name
                target_path = target_folder / item.name
                
                summary[folder_name] += 1
                moved_files.append(f"'{item.name}' -> {folder_name}/")
                
                if not dry_run:
                    target_folder.mkdir(exist_ok=True)
                    try:
                        shutil.move(str(item), str(target_path))
                    except Exception as e:
                        logger.error(f"Dosya taşınamadı {item.name}: {e}")

        total = sum(summary.values())
        msg = f"Masaüstü düzenleme özeti: Toplam {total} dosya{' taşınacak (dry-run)' if dry_run else ' taşındı'}."
        
        return {
            "success": True, 
            "message": msg,
            "details": summary,
            "moved_files": moved_files,
            "dry_run": dry_run
        }

    def summarize_file(self, filepath: str) -> dict:
        """Dosyanın bilgilerini ve metin dosyasıysa ilk 500 karakterini döndürür."""
        path = Path(filepath)
        if not path.exists() or not path.is_file():
            return {"success": False, "message": f"Dosya bulunamadı: {path}"}
            
        try:
            stat = path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            
            content_preview = ""
            if path.suffix.lower() == ".txt":
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content_preview = f.read(500)
            elif path.suffix.lower() == ".pdf":
                content_preview = "(PDF kütüphanesi yapılandırılmadığı için içerik gösterilemiyor. Yalnızca meta bilgisi okundu.)"
            else:
                content_preview = "(Desteklenmeyen dosya türü. İçerik önizlemesi kullanılamıyor.)"
                
            msg = (
                f"Dosya: {path.name}\n"
                f"Boyut: {size_mb:.2f} MB\n"
                f"Son Değiştirilme: {mod_time}\n"
                f"--- İçerik Önizleme ---\n"
                f"{content_preview.strip()}"
                f"{'...' if len(content_preview) == 500 else ''}"
            )
            return {"success": True, "message": msg}
        except Exception as e:
            return {"success": False, "message": f"Dosya okunurken hata oluştu: {e}"}

    def create_readme(self, project_path: str) -> dict:
        """Projeyi tarar ve klasör yapısını içeren temel bir README.md oluşturur."""
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            return {"success": False, "message": "Proje dizini bulunamadı."}
            
        readme_path = path / "README.md"
        
        try:
            folders = []
            files = []
            for item in path.iterdir():
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue
                if item.is_dir():
                    folders.append(item.name)
                elif item.is_file():
                    files.append(item.name)
                    
            content = f"# Proje: {path.name}\n\n"
            content += "## Genel Bakış\n"
            content += "Bu README dosyası JARVIS Asistanı tarafından otomatik olarak oluşturulmuştur.\n\n"
            content += "### Dizin Yapısı\n\n"
            
            content += "**Klasörler:**\n"
            for folder in sorted(folders):
                content += f"- `{folder}/`\n"
                
            content += "\n**Dosyalar:**\n"
            for f in sorted(files):
                content += f"- `{f}`\n"
                
            content += f"\n*Oluşturulma Tarihi: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return {"success": True, "message": f"README.md başarıyla oluşturuldu: {readme_path}"}
        except Exception as e:
            return {"success": False, "message": f"README oluşturulurken hata yaşandı: {e}"}

    def clean_downloads(self, confirm: bool = True) -> dict:
        """İndirilenler klasöründeki 30 günden eski dosyaları listeler ve siler."""
        if not self.downloads_path.exists():
            return {"success": False, "message": f"İndirilenler dizini bulunamadı: {self.downloads_path}"}
            
        now = time.time()
        thirty_days = 30 * 24 * 60 * 60
        old_files = []
        
        for item in self.downloads_path.iterdir():
            if item.is_file():
                if now - item.stat().st_mtime > thirty_days:
                    old_files.append(item)
                    
        if not old_files:
            return {"success": True, "message": "İndirilenler klasöründe 30 günden eski dosya bulunamadı."}
            
        if confirm:
            deleted_count = 0
            for f in old_files:
                try:
                    f.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Silinemedi {f.name}: {e}")
            return {"success": True, "message": f"{deleted_count} adet eski dosya İndirilenler klasöründen silindi."}
        else:
            return {
                "success": True, 
                "message": f"İndirilenler klasöründe silinmeyi bekleyen 30 günden eski {len(old_files)} dosya var. Onay verilmediği için işlem iptal edildi."
            }
