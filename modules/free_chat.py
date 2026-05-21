"""
modules/free_chat.py - JARVIS Serbest Sohbet Modülü
Tanınmayan komutları Mistral 7B üzerinden doğal Türkçe sohbet olarak işler.
Ayrıca arama, dosya oluşturma ve dosya açma gibi basit işlemleri de algılar.
"""

import os
import re
import glob
import logging
import subprocess
import urllib.parse
import difflib
import ollama

logger = logging.getLogger(__name__)

# Opera tarayıcı yolu
OPERA_PATH = r"C:\Users\ibrah\AppData\Local\Programs\Opera\launcher.exe"

# Masaüstü yolu (sabit)
DESKTOP_PATH = r"C:\Users\ibrah\Desktop"

# Sohbet için sistem promptu (JSON formatı yok, doğal konuşma)
FREE_CHAT_SYSTEM_PROMPT = (
    "Sen JARVIS adlı Türkçe bir masaüstü asistansın. "
    "Kullanıcıyla doğal Türkçe konuş. Kısa ve öz cevap ver."
)

# Dosya aranacak klasörler (öncelik sırasına göre)
SEARCH_DIRS = [
    DESKTOP_PATH,
    r"C:\Users\ibrah\Downloads",
    r"C:\Users\ibrah\Documents",
]

# Yaygın dosya uzantıları
FILE_EXTENSIONS = [
    ".txt", ".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg",
    ".jpeg", ".mp4", ".mp3", ".zip", ".rar", ".py", ".html",
    ".csv", ".json", ".xml", ".exe", ".bat",
]

# config.APPS'i import et (uygulama açma için)
try:
    from config import APPS
except ImportError:
    APPS = {}


def _search_google(query: str) -> dict:
    """Opera ile Google'da arama yapar."""
    try:
        # "ara" veya "search" kelimesini ve etrafındaki bağlacları temizle
        clean = query.lower()
        for word in ["ara", "search", "google'da", "googleda", "internette", "bir"]:
            clean = clean.replace(word, "")
        clean = clean.strip().strip("'\"")

        if not clean:
            return {"success": False, "message": "Aranacak metin bulunamadı."}

        search_url = f"https://www.google.com/search?q={urllib.parse.quote(clean)}"

        if os.path.exists(OPERA_PATH):
            subprocess.Popen([OPERA_PATH, search_url])
        else:
            import webbrowser
            webbrowser.open(search_url)

        return {"success": True, "message": f"'{clean}' için Google araması açıldı."}
    except Exception as e:
        logger.error(f"Google arama hatası: {e}")
        return {"success": False, "message": f"Arama yapılamadı: {e}"}


def _create_text_file(text: str) -> dict:
    """Masaüstünde belirtilen isimle txt dosyası oluşturur."""
    try:
        lower = text.lower()

        # Yöntem 1: "kalem isimli/adlı txt dosyası oluştur"
        name_match = re.search(
            r'(\w+)\s+(?:isimli|isimde|adında|adlı|isminde)\s+(?:bir\s+)?(?:txt\s+)?(?:dosya|dosyası)',
            lower,
        )
        if name_match:
            file_name = name_match.group(1)
        else:
            # Yöntem 2: "oluştur" öncesindeki kelimelerden dosya adı çıkar
            parts = lower.split("oluştur")[0].strip().split()
            # Gereksiz kelimeleri filtrele
            skip_words = {"txt", "dosya", "dosyası", "bir", "masaüstüne", "masaüstünde",
                          "masaüstüme", "adlı", "isimli", "adında", "isminde"}
            parts = [p for p in parts if p not in skip_words]
            file_name = parts[-1] if parts else "yeni_dosya"

        # Uzantı yoksa .txt ekle
        if not file_name.endswith(".txt"):
            file_name += ".txt"

        file_path = os.path.join(DESKTOP_PATH, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")

        logger.info(f"Dosya oluşturuldu: {file_path}")
        return {"success": True, "message": f"'{file_name}' dosyası masaüstüne oluşturuldu."}
    except Exception as e:
        logger.error(f"Dosya oluşturma hatası: {e}")
        return {"success": False, "message": f"Dosya oluşturulamadı: {e}"}


def _extract_app_name(text: str) -> str:
    """Komuttan temiz uygulama adını çıkarır."""
    lower = text.lower().strip()
    if "aç" in lower:
        # En sağdaki "aç" kelimesinden öncesini al
        parts = lower.rsplit("aç", 1)
        target = parts[0].strip()
    else:
        target = lower
        
    suffixes = ["uygulamasını", "uygulaması", "programını", "programı", "dosyasını", "dosyayı", "klasörünü", "klasörü", "başlat", "çalıştır"]
    for s in suffixes:
        target = re.sub(rf"\b{s}\b", "", target)
        
    return " ".join(target.split())


def _get_match_score(candidate: str, target: str) -> float:
    """İki uygulama adı arasındaki benzerlik skorunu hesaplar (0.0 - 1.0)."""
    c_low = candidate.lower().strip()
    t_low = target.lower().strip()
    
    if c_low == t_low:
        return 1.0
        
    c_words = set(c_low.split())
    t_words = set(t_low.split())
    
    if t_words and t_words.issubset(c_words):
        word_ratio = len(t_words) / len(c_words)
        return 0.8 + (word_ratio * 0.15)
        
    if c_words and c_words.issubset(t_words):
        word_ratio = len(c_words) / len(t_words)
        return 0.75 + (word_ratio * 0.15)
        
    if t_low in c_low:
        return 0.7
    if c_low in t_low:
        return 0.65
        
    return difflib.SequenceMatcher(None, c_low, t_low).ratio()


def _open_app_or_file(text: str) -> dict:
    """
    "aç" içeren komutları işler:
    1) Önce config.APPS'te uygulama arar (hata durumunda aramaya devam eder)
    2) Bulunamazsa Windows Başlat Menüsü ve Masaüstü kısayollarında otomatik arar (.lnk)
    3) Sonra Desktop, Downloads, Documents'ta dosya arar
    4) Bulunamazsa hata döndürür
    """
    try:
        lower = text.lower().strip()

        # ── 1) config.APPS'te uygulama ara ──────────────────────────────
        for app_name, app_path in APPS.items():
            if app_name in lower:
                logger.info(f"APPS eşleşmesi: '{app_name}' → {app_path}")
                try:
                    if app_path.startswith("shell:"):
                        os.startfile(app_path)
                        return {"success": True, "message": f"'{app_name}' uygulaması açıldı."}
                    elif os.path.exists(app_path):
                        subprocess.Popen([app_path])
                        return {"success": True, "message": f"'{app_name}' uygulaması açıldı."}
                    else:
                        logger.warning(f"APPS yolunda dosya bulunamadı: {app_path}. Kısayol aramasına geçiliyor...")
                except Exception as e:
                    logger.error(f"APPS açma hatası: {e}. Kısayol aramasına geçiliyor...")

        # ── 2) Windows Başlat Menüsü ve Masaüstü Kısayollarında Ara ──────────
        app_target = _extract_app_name(text)
        if app_target:
            logger.info(f"Kısayollarda uygulama aranıyor: '{app_target}'")
            SHORTCUT_DIRS = [
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
                r"C:\Users\ibrah\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
                DESKTOP_PATH,
            ]
            
            best_match = None
            best_score = 0.0
            
            for start_dir in SHORTCUT_DIRS:
                if not os.path.exists(start_dir):
                    continue
                    
                for root, _, files in os.walk(start_dir):
                    for file in files:
                        if file.lower().endswith(".lnk"):
                            shortcut_path = os.path.join(root, file)
                            candidate_name = os.path.splitext(file)[0]
                            
                            score = _get_match_score(candidate_name, app_target)
                            if score > best_score:
                                best_score = score
                                best_match = (candidate_name, shortcut_path)
            
            # Eşleşme hassasiyeti için 0.70 barajı (örn. Visual Studio Code için Android Studio açılmasın)
            if best_match and best_score >= 0.70:
                matched_name, shortcut_path = best_match
                logger.info(f"Kısayol eşleşmesi bulundu: '{matched_name}' (Skor: {best_score:.2f}) → {shortcut_path}")
                os.startfile(shortcut_path)
                return {"success": True, "message": f"'{matched_name}' uygulaması açıldı."}

        # ── 3) Dosya adını metinden çıkar ────────────────────────────────
        search_name = None

        # "kalem.txt dosyasını aç" veya "kalem txt dosyasını aç"
        # İlk olarak uzantılı dosya adını ara
        file_match = re.search(r'([\w\-]+)\.([\w]+)', text)
        if file_match:
            search_name = f"{file_match.group(1)}.{file_match.group(2)}"
        else:
            # "kalem txt dosyasını aç" → "kalem" + ".txt"
            txt_match = re.search(r'([\w\-]+)\s+txt\b', lower)
            if txt_match:
                search_name = f"{txt_match.group(1)}.txt"
            else:
                # "kalem dosyasını aç" → "kalem"
                name_match = re.search(
                    r'([\w\-]+)\s+(?:dosyasını|dosyayı|dosyası)',
                    lower,
                )
                if name_match:
                    search_name = name_match.group(1)
                else:
                    # Son deneme: "aç" kelimesinden önceki son kelimeyi al
                    parts = lower.split("aç")[0].strip().split()
                    skip = {"masaüstündeki", "masaüstünde", "masaüstümdeki",
                            "dosyasını", "dosyayı", "bir", "txt"}
                    parts = [p for p in parts if p not in skip]
                    if parts:
                        search_name = parts[-1]

        if not search_name:
            return {"success": False, "message": "Açılacak dosya veya uygulama adı bulunamadı."}

        # Gereksiz kelimeleri temizle
        skip_words = {"masaüstündeki", "masaüstünde", "dosyasını", "dosyayı"}
        if search_name in skip_words:
            return {"success": False, "message": "Açılacak dosya adı bulunamadı."}

        logger.info(f"Dosya aranıyor: '{search_name}'")

        # ── 3) Dosya ara: Desktop → Downloads → Documents ───────────────
        for search_dir in SEARCH_DIRS:
            if not os.path.exists(search_dir):
                continue

            # Tam eşleşme
            full_path = os.path.join(search_dir, search_name)
            if os.path.exists(full_path):
                os.startfile(full_path)
                return {"success": True, "message": f"'{search_name}' dosyası açıldı."}

            # Uzantısızsa tüm uzantıları dene
            if "." not in search_name:
                for ext in FILE_EXTENSIONS:
                    test_path = os.path.join(search_dir, f"{search_name}{ext}")
                    if os.path.exists(test_path):
                        found_name = os.path.basename(test_path)
                        os.startfile(test_path)
                        return {"success": True, "message": f"'{found_name}' dosyası açıldı."}

            # Glob ile alt klasörlerde ara
            if "." in search_name:
                pattern = os.path.join(search_dir, "**", search_name)
            else:
                pattern = os.path.join(search_dir, "**", f"{search_name}.*")
            matches = glob.glob(pattern, recursive=True)
            if matches:
                found_name = os.path.basename(matches[0])
                os.startfile(matches[0])
                return {"success": True, "message": f"'{found_name}' dosyası açıldı."}

        return {"success": False, "message": f"'{search_name}' dosyası veya uygulaması bulunamadı."}
    except Exception as e:
        logger.error(f"Dosya/uygulama açma hatası: {e}")
        return {"success": False, "message": f"Açılamadı: {e}"}


def _chat_with_llm(text: str) -> dict:
    """Mistral 7B ile doğal sohbet yapar (JSON formatı olmadan)."""
    try:
        response = ollama.chat(
            model="mistral:7b",
            messages=[
                {"role": "system", "content": FREE_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            options={
                "temperature": 0.7,
                "num_predict": 512,
            },
        )

        reply = response["message"]["content"].strip()
        logger.info(f"Free chat yanıtı: {reply[:100]}...")
        return {"success": True, "message": reply}
    except Exception as e:
        logger.error(f"Free chat LLM hatası: {e}")
        return {"success": False, "message": f"Sohbet hatası: {e}"}


def execute(text: str) -> dict:
    """
    Serbest sohbet ana fonksiyonu.
    Metni analiz ederek arama, dosya oluşturma, dosya/uygulama açma veya
    doğal sohbet işlemlerinden birini gerçekleştirir.

    Öncelik sırası:
    1) "ara" / "search" → Google araması
    2) "oluştur" + "txt" → Masaüstünde dosya oluştur
    3) "aç" → config.APPS kontrol → Desktop/Downloads/Documents'ta dosya ara
    4) Fallback → Mistral 7B doğal sohbet

    Args:
        text: Kullanıcının ham Türkçe metni.

    Returns:
        dict: {"success": True/False, "message": "<yanıt>"}
    """
    lower = text.lower().strip()

    # 1) Arama algılama: "ara" veya "search" içeriyorsa
    if "ara" in lower.split() or "search" in lower.split() or "arat" in lower.split():
        logger.info(f"Arama algılandı: {text}")
        return _search_google(text)

    # 2) Dosya oluşturma: "oluştur" ve ("txt" veya "dosya")
    if "oluştur" in lower and ("txt" in lower or "dosya" in lower):
        logger.info(f"Dosya oluşturma algılandı: {text}")
        return _create_text_file(text)

    # 3) "aç" komutu: önce APPS, sonra dosya arama
    if "aç" in lower:
        logger.info(f"Açma komutu algılandı: {text}")
        return _open_app_or_file(text)

    # 4) Fallback: Doğal sohbet (Mistral 7B)
    logger.info(f"Serbest sohbet moduna geçiliyor: {text}")
    return _chat_with_llm(text)
