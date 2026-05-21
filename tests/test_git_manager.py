import sys

def main():
    from modules.git_manager import GitManager
    
    # Varsayılan olarak bulunduğu dizini alır
    manager = GitManager()
    
    print("\n--- TEST 1: git_status() ---")
    res1 = manager.git_status()
    print(res1)
    
    print("\n--- TEST 2: git_push('test commit mesajı') ---")
    res2 = manager.git_push("test commit mesajı")
    print(res2)
    
    print("\n--- TEST 3: git_pull() ---")
    res3 = manager.git_pull()
    print(res3)

if __name__ == "__main__":
    main()
