import sys
import os

def main():
    print("=== DAILY SUMMARY TEST ===")
    from modules.daily_summary import DailySummary
    daily = DailySummary()
    
    summary_text = daily.generate_summary()
    print("Günlük Özet:")
    print(summary_text)

    print("\n=== PROMPT GENERATOR TEST ===")
    from modules.prompt_generator import PromptGenerator
    pg = PromptGenerator(model_name="mistral:7b") # Veya cihazda olan geçerli bir model: llama3.2:3b
    
    # Ollama yüklü ve çalışıyorsa bu çalışır:
    changed_files = ["core/memory.py", "core/context.py"]
    print(f"Değişen Dosyalar: {changed_files}")
    res = pg.generate_commit_message(changed_files)
    
    if res["success"]:
        print("Üretilen Commit Mesajı:", res["message"])
    else:
        print("Hata:", res["message"])

if __name__ == "__main__":
    main()
