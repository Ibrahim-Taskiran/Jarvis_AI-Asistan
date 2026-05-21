import sys

def main():
    print("=== BROWSER MANAGER TEST ===")
    from modules.browser_manager import BrowserManager
    browser = BrowserManager()
    
    # 1) Doğrudan url
    res_b1 = browser.open_url("python.org")
    print(f"open_url('python.org') -> {res_b1}")
    
    # 2) Mapping üzerinden
    res_b2 = browser.open_site("okul")
    print(f"open_site('okul') -> {res_b2}")

    print("\n=== MEDIA MANAGER TEST ===")
    from modules.media_manager import MediaManager
    media = MediaManager()
    
    # play_pause
    res_m1 = media.media_control("şarkıyı başlat")
    print(f"media_control('şarkıyı başlat') -> {res_m1}")
    
    # volume up
    res_m2 = media.media_control("sesi arttır")
    print(f"media_control('sesi arttır') -> {res_m2}")

    print("\n=== TERMINAL MANAGER TEST ===")
    from modules.terminal_manager import TerminalManager
    terminal = TerminalManager()
    
    # Basit echo komutu
    res_t1 = terminal.run_command("echo JARVIS Terminal Test")
    print(f"run_command('echo JARVIS Terminal Test') -> {res_t1}")
    
    # Pip freeze / requirements
    res_t2 = terminal.create_requirements()
    print(f"create_requirements() -> {res_t2}")

if __name__ == "__main__":
    main()
