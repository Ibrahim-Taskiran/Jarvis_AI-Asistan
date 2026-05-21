"""
modules/prompt_generator.py - Prompt ve Commit Mesajı Üretici
Projelerin yapısına veya değişen dosyalara bakarak AI destekli (Ollama) metinler üretir.
"""

import os
import logging
import ollama
from pathlib import Path

# Config'i projenin kök dizininden içe aktarabilmek için
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import COMPLEX_MODEL

logger = logging.getLogger(__name__)

class PromptGenerator:
    """LLM kullanarak geliştirme promptları ve commit mesajları üretir."""

    def __init__(self, model_name=COMPLEX_MODEL):
        self.model = model_name

    def generate_project_prompt(self, project_path: str) -> dict:
        """Projeyi tarayarak Cursor/Windsurf için geliştirme promptu üretir."""
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            return {"success": False, "message": "Proje dizini bulunamadı."}
            
        structure = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'venv', 'node_modules')]
            level = str(root).replace(str(path), '').count(os.sep)
            indent = ' ' * 4 * level
            structure.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if not f.startswith('.'):
                    structure.append(f"{subindent}{f}")
                    
        structure_text = "\n".join(structure)
        
        # README varsa özetini al
        readme_content = ""
        readme_path = path / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read(1000)
            except:
                pass
                
        system_prompt = (
            "Sen uzman bir yazılım mimarısın. Verilen proje yapısı ve README özetine dayanarak, "
            "yapay zeka kod asistanları (Cursor/Windsurf vb.) için çok detaylı, yapılandırılmış ve "
            "profesyonel bir Türkçe 'geliştirme promptu' hazırla. "
            "Mevcut duruma göre sonraki en mantıklı geliştirme adımını tarif et."
        )
        
        user_message = f"Proje Yapısı:\n{structure_text}\n\n"
        if readme_content:
            user_message += f"README Özeti:\n{readme_content}\n"
            
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            result_text = response.get("message", {}).get("content", "")
            return {"success": True, "message": result_text.strip()}
        except Exception as e:
            logger.error(f"Prompt hatası: {e}")
            return {"success": False, "message": f"Yapay zeka ile bağlantı kurulamadı: {e}"}

    def generate_commit_message(self, changed_files: list[str]) -> dict:
        """Değişen dosya listesinden profesyonel bir commit mesajı çıkarır."""
        if not changed_files:
            return {"success": False, "message": "Değişen dosya listesi boş."}
            
        files_str = "\n".join(changed_files)
        
        system_prompt = (
            "Sana projedeki değişen veya eklenen dosyaların listesi verilecek. "
            "Sadece bu dosya isimlerine bakarak kısa, öz ve profesyonel bir Türkçe git commit mesajı yaz. "
            "Mesaj tek cümle olmalı ve sadece commit mesajını içermelidir (başka bir yorum veya açıklama ekleme)."
        )
        
        user_message = f"Değişen Dosyalar:\n{files_str}"
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            result_text = response.get("message", {}).get("content", "")
            return {"success": True, "message": result_text.strip()}
        except Exception as e:
            logger.error(f"Commit mesajı hatası: {e}")
            return {"success": False, "message": f"Yapay zeka ile bağlantı kurulamadı: {e}"}
