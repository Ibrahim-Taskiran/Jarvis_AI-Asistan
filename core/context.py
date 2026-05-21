"""
core/context.py - JARVIS Bağlam Yöneticisi
Kullanıcının o an aktif olarak kullandığı pencereyi ve projeyi tespit eder.
"""

import logging
import psutil
try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from core.memory import MemoryManager

logger = logging.getLogger(__name__)

class ContextManager:
    """Aktif pencereyi ve bağlam bilgisini yöneten sınıf."""

    def __init__(self, memory_manager: MemoryManager = None):
        self.memory = memory_manager or MemoryManager()

    def get_active_window(self) -> str:
        """Kullanıcının o an odaklandığı pencerenin başlığını döndürür."""
        if not WIN32_AVAILABLE:
            return "win32gui yüklü değil"
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                return win32gui.GetWindowText(hwnd)
            return ""
        except Exception as e:
            logger.error(f"Aktif pencere bulunamadı: {e}")
            return ""

    def get_active_process_name(self) -> str:
        """Aktif pencerenin işlem adını (exe) döndürür."""
        if not WIN32_AVAILABLE:
            return ""
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                return proc.name()
            return ""
        except Exception as e:
            return ""

    def get_active_project(self) -> str | None:
        """Aktif pencere Cursor veya VSCode ise proje klasör adını ayıklar."""
        title = self.get_active_window()
        process_name = self.get_active_process_name().lower()
        
        if not title:
            return None
            
        title_lower = title.lower()
        # Pencere başlığında veya process adında cursor/code arayalım
        is_editor = "cursor" in title_lower or "visual studio code" in title_lower or "cursor.exe" in process_name or "code.exe" in process_name
        
        if is_editor:
            # Örnek Başlık: "main.py - Jarvis - Visual Studio Code" veya "context.py - Jarvis - Cursor"
            parts = title.split(" - ")
            if len(parts) >= 2:
                # Genelde sondan bir önceki bölüm proje adıdır
                for p in reversed(parts):
                    p_lower = p.lower()
                    if "cursor" not in p_lower and "visual studio" not in p_lower:
                        return p.strip()
        return None

    def get_context_summary(self) -> dict:
        """Aktif pencere, aktif proje ve en son komutu içeren bir özet döndürür."""
        active_window = self.get_active_window()
        active_project = self.get_active_project()
        
        last_cmd = self.memory.get_last_command()
        last_action = last_cmd["action"] if last_cmd else None
        
        return {
            "active_window": active_window,
            "active_project": active_project,
            "last_command": last_action
        }
