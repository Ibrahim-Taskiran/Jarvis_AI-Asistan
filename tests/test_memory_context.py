import sys

def main():
    print("=== MEMORY MANAGER TEST ===")
    from core.memory import MemoryManager
    memory = MemoryManager()
    
    # Yeni bir komut kaydet
    memory.save_command(
        raw_text="spotify'ı aç",
        action="open_app",
        params={"app": "spotify"},
        result="Spotify başarıyla açıldı.",
        model_used="llama3.2:3b",
        response_time=1.45
    )
    
    # İkinci komut kaydet
    memory.save_command(
        raw_text="şu anki projeyi çalıştır",
        action="run_terminal",
        params={"cmd": "python main.py"},
        result="Başlatıldı",
        model_used="mistral:7b",
        response_time=3.20
    )

    last_cmd = memory.get_last_command()
    print("En Son Komut:", dict(last_cmd) if last_cmd else None)

    last_app = memory.get_last_opened_app()
    print("En Son Açılan Uygulama:", last_app)

    history = memory.get_history(limit=2)
    print(f"Geçmiş (son 2): {len(history)} kayıt")


    print("\n=== CONTEXT MANAGER TEST ===")
    from core.context import ContextManager
    context = ContextManager(memory)
    
    active_win = context.get_active_window()
    print("Aktif Pencere:", active_win)
    
    active_proj = context.get_active_project()
    print("Aktif Proje (Cursor/VSCode ise):", active_proj)
    
    summary = context.get_context_summary()
    print("Bağlam Özeti:", summary)

if __name__ == "__main__":
    main()
