import os

def main():
    from modules.file_manager import FileManager
    fm = FileManager()
    
    print("\n=== TEST 1: summarize_file ===")
    # Bir test dosyası oluştur
    test_txt = "test_summary.txt"
    with open(test_txt, "w", encoding="utf-8") as f:
        f.write("Bu bir test metnidir. " * 30) # ~600 karakter
        
    res_s = fm.summarize_file(test_txt)
    print(res_s["message"])
    
    # Test dosyasını temizle
    if os.path.exists(test_txt):
        os.remove(test_txt)
        
    print("\n=== TEST 2: create_readme ===")
    res_r = fm.create_readme("C:/Users/ibrah/Documents/GitHub/Jarvis")
    print(res_r)
    
    print("\n=== TEST 3: organize_desktop (dry-run) ===")
    res_o = fm.organize_desktop(dry_run=True)
    print(res_o["message"])
    if res_o["moved_files"]:
        print("Taşınacak bazı dosyalar:")
        for f in res_o["moved_files"][:5]:
            print("  ", f)

if __name__ == "__main__":
    main()
