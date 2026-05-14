"""
modules/git_manager.py - Git Yöneticisi
Git depoları için add, commit, push, pull, fetch ve status işlemlerini yapar.
"""

import os
import datetime
import logging
from git import Repo, InvalidGitRepositoryError

logger = logging.getLogger(__name__)

class GitManager:
    """Git işlemlerini yöneten sınıf."""
    
    def __init__(self, repo_path: str = None):
        if repo_path is None:
            # Otomatik algılama için geçerli dizini kullanır (Jarvis kök dizini)
            repo_path = os.getcwd()
            
        self.repo_path = repo_path
        self.repo = self._get_repo()

    def _get_repo(self) -> Repo | None:
        """Verilen yolda veya üst dizinlerde geçerli bir git deposu arar."""
        try:
            return Repo(self.repo_path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            return None

    def git_status(self) -> dict:
        """Git deposunun durumunu döndürür."""
        if not self.repo:
            return {"success": False, "message": "Git deposu bulunamadı"}
            
        try:
            # Değiştirilmiş ve yeni eklenmiş dosyalar
            changed_files = [item.a_path for item in self.repo.index.diff(None)]
            untracked_files = self.repo.untracked_files
            
            total_changes = len(changed_files) + len(untracked_files)
            
            if total_changes == 0:
                # Commitlenmemiş bir eklenti (staged changes) var mı kontrol et
                if self.repo.is_dirty(untracked_files=True) or self.repo.index.diff(self.repo.head.commit):
                    message = "Commit edilmeyi bekleyen değişiklikler var."
                else:
                    message = "Çalışma alanı temiz. Herhangi bir değişiklik yok."
            else:
                message = f"Toplam {total_changes} değiştirilmiş veya yeni eklenmiş dosya var."
                
            return {"success": True, "message": message, "changes": total_changes}
        except Exception as e:
            logger.error(f"git status hatası: {e}")
            return {"success": False, "message": "Durum kontrol edilirken bir hata oluştu."}

    def git_push(self, commit_message: str = None) -> dict:
        """Tüm değişiklikleri ekler, commit eder ve uzak sunucuya gönderir."""
        if not self.repo:
            return {"success": False, "message": "Git deposu bulunamadı"}
            
        try:
            # 1. Add all
            self.repo.git.add(A=True)
            
            # Değişiklik var mı kontrol et
            if not self.repo.is_dirty(untracked_files=True) and not self.repo.index.diff(self.repo.head.commit):
                # Gönderilmemiş commit var mı kontrol et
                active_branch = self.repo.active_branch
                tracking_branch = active_branch.tracking_branch()
                if tracking_branch:
                    commits_ahead = list(self.repo.iter_commits(f'{tracking_branch.name}..{active_branch.name}'))
                    if len(commits_ahead) == 0:
                        return {"success": True, "message": "Gönderilecek yeni bir değişiklik veya commit yok."}
                else:
                    return {"success": True, "message": "Gönderilecek yeni bir değişiklik yok."}
            else:
                # 2. Commit
                if not commit_message:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    commit_message = f"JARVIS: otomatik commit - {now}"
                    
                self.repo.index.commit(commit_message)
            
            # 3. Push
            origin = self.repo.remote(name='origin')
            origin.push()
            
            return {"success": True, "message": "Değişiklikler başarıyla uzak sunucuya gönderildi."}
        except Exception as e:
            logger.error(f"git push hatası: {e}")
            return {"success": False, "message": f"Push işlemi sırasında hata oluştu: {str(e)}"}

    def git_pull(self) -> dict:
        """Uzak sunucudan değişiklikleri çeker."""
        if not self.repo:
            return {"success": False, "message": "Git deposu bulunamadı"}
            
        try:
            origin = self.repo.remote(name='origin')
            origin.pull()
            return {"success": True, "message": "Uzak sunucudaki değişiklikler başarıyla çekildi."}
        except Exception as e:
            logger.error(f"git pull hatası: {e}")
            return {"success": False, "message": f"Pull işlemi sırasında hata oluştu."}

    def git_fetch(self) -> dict:
        """Fetch işlemi yapar ve uzak sunucuda yeni commit olup olmadığını kontrol eder."""
        if not self.repo:
            return {"success": False, "message": "Git deposu bulunamadı"}
            
        try:
            origin = self.repo.remote(name='origin')
            origin.fetch()
            
            # Uzak sunucudaki yeni commitleri kontrol et
            active_branch = self.repo.active_branch
            tracking_branch = active_branch.tracking_branch()
            
            if tracking_branch:
                commits_behind = list(self.repo.iter_commits(f'{active_branch.name}..{tracking_branch.name}'))
                
                if len(commits_behind) > 0:
                    message = f"Fetch tamamlandı. Uzak sunucuda {len(commits_behind)} yeni commit var. Güncellemek için pull yapmalısınız."
                else:
                    message = "Fetch tamamlandı. Çalışma alanınız güncel."
            else:
                message = "Fetch tamamlandı. (Uzak sunucuda izlenen bir dal bulunamadı)"
                
            return {"success": True, "message": message}
        except Exception as e:
            logger.error(f"git fetch hatası: {e}")
            return {"success": False, "message": f"Fetch işlemi sırasında hata oluştu."}
