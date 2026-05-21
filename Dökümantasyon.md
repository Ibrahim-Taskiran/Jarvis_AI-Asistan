JARVIS — K!ş!sel Masaüstü Yapay Zeka As!stanı
F!nal Tekn!k Dokümantasyon v2.0
1. Proje K!ml!ğ!
Özell!k
Detay
İşlet#m S#stem#
W#ndows 11
Donanım
HP V#ctus 16, RTX 3060 (6GB VRAM), 16GB RAM, 1.5TB SSD
G#r#ş Yöntem#
Yalnızca sesl# komut (Türkçe)
Çıkış Yöntem#
Sesl# yanıt + masaüstü pencere
Arayüz
Masaüstünde sab#t, küçük görünür pencere
Ver# G#zl#l#ğ#
Tamamen yerel (local), #nternet bağlantısı gerekmez
Mal#yet
Sıfır (Cursor ve Spot#fy abonel#kler# har#ç)
2. S!stem M!mar!s!
[Mikrofon]
↓
[Whisper Medium — Türkçe Ses → Metin]
↓
[Model Router — Komut Karmaşıklığı Analizi]
↓                        
↓
[Llama 3.2 3B]        [Mistral 7B]
(Basit komutlar)      (Karmaşık görevler)
↓                        
↓
[Python Komut Yönlendirici (Router)]
↓
[İlgili Modül Çalışır]
↓
[TTS — Sesli Yanıt] + [PyQt6 Arayüz Güncellenir]
3. Teknoloj! Yığını (Stack)
Katman Teknoloj! Gerekçe
Ses Tanıma faster-wh#sper
(med#um)
Türkçe #ç#n en #y# yerel model, GPU
hızlandırmalı
LLM — Hızlı Ollama + Llama 3.2 3B Bas#t komutlar #ç#n ~1 sn yanıt
LLM — Akıllı Ollama + M#stral 7B Prompt üretme, kod anal#z#, doküman #şler#
Sesl# Yanıt pyttsx3 Tamamen yerel TTS, #nternet gerekt#rmez
Arayüz PyQt6 Masaüstü pencere, haf#f ve stab#l
OS İşlemler# subprocess, os, pathl#b W#ndows s#stem komutları
G#t G#tPython G#t #şlemler#n# Python’dan yönetme
Hafıza SQL#te Yerel, sıfır mal#yet, depolama dostu
Log Python logg#ng Düşük boyutlu, tar#h bazlı log dosyaları
Gel#şt#rme
IDE Cursor / W#ndsurf AI destekl# gel#şt#rme ortamı
4. Model Router Mantığı
SIMPLE_COMMANDS = ["open_app", "close_app", "shutdown", "restart",
                   "volume", "git_push", "git_pull", "open_browser",
                   "media_control", "run_terminal"]
COMPLEX_COMMANDS = ["generate_prompt", "analyze_code", "summarize_file",
                    "create_readme", "organize_files", "daily_summary"]
# Basit → Llama 3.2 3B  (~1 sn)
# Karmaşık → Mistral 7B  (~3-5 sn)
Öneml!: İk# model aynı anda RAM’de durmaz. Ollama hang#s# çağrılırsa yükler, #ş# b#t#nce
boşaltır. 6GB VRAM #ç#n sorun yok.
5. Özell!kler ve Modüller
Modül 1: Uygulama ve S!stem Yönet!m!
Komut örnekler!:
“CS2’y# aç” / “Spot#fy’ı kapat”
“B#lg#sayarı kapat” (onay sorar)
“Ses# yüzde ell# yap”
“Yen#den başlat” (onay sorar)
Model: Llama 3.2 3B
Modül 2: G!t Otomasyonu
Komut örnekler!:
“Projey# G#tHub’a yükle” → add + comm#t + push
“Yen# comm#t var mı?” → g#t status
“Takım arkadaşlarından push var mı?” → g#t fetch + log
“Değ#ş#kl#kler# çek” → g#t pull
“Comm#t mesajı: arayüz güncellend#”
Model: Llama 3.2 3B Not: Comm#t mesajı bel#rt#lmezse M#stral otomat#k üret#r.
Modül 3: IDE ve Proje Yönet!m!
Komut örnekler!:
“Cursor’ı aç”
“Hesap mak#nes# adında yen# proje oluştur”
“Bu proje #ç#n prompt ver” → M#stral prompt üret#r, ekranda göster#r
Model: Llama 3.2 3B (açma) / M#stral 7B (prompt üretme)
Modül 4: Term!nal Otomasyonu
Komut örnekler!:
“P#p paketler#n# güncelle”
“V#rtual env#ronment oluştur”
“Requ#rements dosyası oluştur”
Model: Llama 3.2 3B
Modül 5: Dosya ve Belge İşlemler!
Komut örnekler!:
“Masaüstünü düzenle”
“Bu PDF’# özetle”
“Proje #ç#n README oluştur”
“İnd#r#lenler klasörünü tem#zle” (onay sorar)
Model: M#stral 7B
Modül 6: Tarayıcı Kontrolü
Komut örnekler!:
“YouTube’u aç”
“G#tHub’ı Opera’da aç”
“Okul s#stem#n# aç”
Model: Llama 3.2 3B
Modül 7: Müz!k ve Medya Kontrolü
Komut örnekler!:
“Müz#ğ# durdur / devam ett#r”
“Sonrak# şarkıya geç”
“Ses kıs”
Model: Llama 3.2 3B Tekn!k: pyautogu# klavye kısayolları (ücrets#z, Spot#fy Prem#um
gerekt#rmez)
Modül 8: Hafıza S!stem!
Ne yapar:
Her komut ve sonucu SQL#te ver#tabanına kaydeder
“Dün açtığım projeye dön” g#b# geçm#şe dayalı komutlar çalışır
Hang# uygulamanın ne zaman açıldığını hatırlar
Depolama: Günlük ~50-100 KB. 1 yıl = ~35 MB. Sorun yok.
Modül 9: Bağlam Farkındalığı
Ne yapar:
O an hang# uygulamanın akt#f olduğunu #zler
Hang# projede çalıştığını otomat#k algılar
“Bu projey# G#tHub’a yükle” dersen hang# klasörü kastett#ğ#n# b#l#r
Tekn!k: psutil + win32gui #le akt#f pencere tak#b#
Modül 10: Günlük Özet (Startup Rut!n!)
Ne yapar:
B#lg#sayar açılınca otomat#k çalışır
G#t repolarındak# son comm#t durumunu kontrol eder
Sesl# olarak günlük özet sunar: “Günaydın. Dün 3 comm!t yaptın. hesap_mak!nes!
projes!nde değ!şt!r!lmem!ş 2 dosya var.”
Model: M#stral 7B
Modül 11: Onay S!stem!
Tehl!kel! komutlarda devreye g!rer:
B#lg#sayarı kapat / yen#den başlat
Dosya veya klasör s#lme
G#t force push
Akış:
Komut gelir → Tehlikeli mi? → Sesli sorar: "Emin misin?"
→ "Evet" → Çalışır
→ "Hayır" / sessizlik → İptal
Modül 12: Uyku Modu
Mantık:
10 dak#ka komut gelmezse Wh#sper d#nlemey# durdurur
Ollama model# RAM’den boşaltılır
Arayüzde “Uyku modunda” yazar
Herhang# b#r ses gel#nce otomat#k uyanır
Faydası: Oyun oynarken veya v#deo #zlerken GPU/RAM boşta kalmaz.
Modül 13: Log S!stem!
Özell!kler:
Her komut, model seç#m#, süre ve sonuç kayded#l#r
Günlük log dosyası: logs/2025-01-15.log
30 günden esk# loglar otomat#k s#l#n#r
Boyut: günlük ~10-20 KB
6. Proje Klasör Yapısı
jarvis/
├── main.py                    # Ana başlatıcı
├── config.py                  # Tüm ayarlar
├── requirements.txt
├── data/
│   
├── memory.db              # SQLite hafıza
│   
└── logs/                  # Günlük log dosyaları
├── core/
│   
│   
│   
│   
│   
│   
│   
├── listener.py            # Whisper ses dinleme
├── brain.py               # Ollama LLM entegrasyonu
├── router.py              # Model + modül yönlendirici
├── memory.py              # Hafıza sistemi
├── context.py             # Bağlam farkındalığı
├── tts.py                 # Sesli yanıt (pyttsx3)
└── safety.py              # Onay sistemi
├── modules/
│   
│   
│   
│   
│   
│   
│   
│   
├── app_manager.py         # Uygulama aç/kapat
├── git_manager.py         # Git işlemleri
├── terminal_manager.py    # Terminal komutları
├── file_manager.py        # Dosya işlemleri
├── browser_manager.py     # Tarayıcı kontrolü
├── media_manager.py       # Spotify / ses
├── daily_summary.py       # Günlük özet
└── prompt_generator.py    # Cursor/IDE için prompt üretme
└── ui/
└── window.py              # PyQt6 masaüstü pencere
7. Arayüz (PyQt6 Pencere)
┌─────────────────────────────┐
│   JARVIS                  
│
│─────────────────────────────│
│  Durum: Dinleniyor...       
│
│                             
│  Son komut:                 
│  "Projeyi GitHub'a yükle"  │
│                             
│  Sonuç:                     
│   Push tamamlandı         
│
│
│
│
│
│─────────────────────────────│
│  Model: Llama 3B  |  0.9sn  │
└─────────────────────────────┘
Masaüstünde her zaman görünür, üstte sab#t
Sağ tıkla: Uyku modu / Kapat seçenekler#
Renk: D#nlen#yor (mav#) / İşlen#yor (sarı) / Tamamlandı (yeş#l) / Hata (kırmızı)
8. LLM S!stem Promptu
Sen JARVIS adlı Türkçe bir masaüstü asistansın.
Kullanıcının sesli komutlarını analiz et ve YALNIZCA JSON döndür.
Format:
{"action": "open_app", "params": {"app": "spotify"}, "confirm": false}
"confirm: true" yalnızca tehlikeli işlemlerde (shutdown, delete, force_push).
Mevcut aksiyonlar:
open_app, close_app, shutdown, restart, volume_control,
git_push, git_pull, git_status, git_fetch,
run_terminal, open_browser, media_control,
organize_files, summarize_file, create_readme,
generate_prompt, daily_summary
Bağlam: {active_window} | Son komut: {last_command}
9. Kurulum Adımları
Adım 1: Ollama
# https://ollama.com adresinden indir ve kur
ollama pull llama3.2:3b
ollama pull mistral:7b
Adım 2: Python Ortamı
python -m venv jarvis_env
jarvis_env\Scripts\activate
pip install faster-whisper gitpython pyautogui PyQt6
pip install pyttsx3 psutil pywin32 requests keyboard sqlite3
Adım 3: conf!g.py
APPS = {
    "cs2": "C:/Program Files (x86)/Steam/.../cs2.exe",
    "spotify": "C:/Users/[kullanıcı]/AppData/Roaming/Spotify/Spotify.exe",
    "opera": "C:/Users/[kullanıcı]/AppData/Local/Programs/Opera/launcher.exe",
    "cursor": "C:/Users/[kullanıcı]/AppData/Local/Programs/cursor/Cursor.exe",
}
DEFAULT_GIT_PATH = "C:/Users/[kullanıcı]/Projects"
WHISPER_LANGUAGE = "tr"
WHISPER_MODEL = "medium"
SLEEP_TIMEOUT_MINUTES = 10
LOG_RETENTION_DAYS = 30
SIMPLE_MODEL = "llama3.2:3b"
COMPLEX_MODEL = "mistral:7b"
10. Gel!şt!rme Planı
Aşama İçer!k Süre
1 Ollama kurulum + #k# model test# 1 gün
2 Wh#sper ses tanıma + Türkçe test 1 gün
3 Model Router (bas#t/karmaşık ayrımı) 1 gün
4 Uygulama açma/kapama + onay s#stem# 1-2 gün
5 PyQt6 arayüz + TTS sesl# yanıt 2 gün
6 G#t modülü 1 gün
7 Hafıza s#stem# (SQL#te) 1-2 gün
8 Bağlam farkındalığı 1 gün
9 Term#nal + dosya modüller# 2 gün
10 Tarayıcı + medya modüller# 1 gün
11 Prompt üret#c# modülü 1 gün
12 Günlük özet + uyku modu + log 1-2 gün
13
Test ve #nce ayar
3 gün
Toplam tahm!n! süre: ~3 hafta
11. requ!rements.txt
faster-whisper
gitpython
pyautogui
PyQt6
pyttsx3
psutil
pywin32
requests
keyboard
ollama
12. B!l!nen Kısıtlamalar
Kısıt
Açıklama
Cursor/W#ndsurf
AI
JARVIS bu uygulamaların AI kutusuna otomat#k yazamaz — sadece
prompt üret#r, sen yapıştırırsın
M#stral 7B
İlk yüklemede 2-3 sn gec#kme olur, sonrak# çağrılar hızlıdır
Türkçe LLM
S#stem promptu İng#l#zce yazılmalı, Llama/M#stral Türkçey# anlar ama
İng#l#zcede daha güçlüdür
Spot#fy kontrolü
pyautogu# klavye kısayolları #le yapılır, Prem#um gerekt#rmez
JARVIS v2.0 F!nal Dokümantasyon — Tüm özell!kler onaylanmış ve kapsanmıştır