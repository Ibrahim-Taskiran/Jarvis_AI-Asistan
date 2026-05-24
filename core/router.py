"""
core/router.py - JARVIS Komut Yönlendirici
Gelen aksiyonu analiz ederek hangi modelin (simple/complex)
ve hangi modülün kullanılacağına karar verir.
"""

import logging

logger = logging.getLogger(__name__)

# ── Model Sınıflandırması ────────────────────────────────────────────────────
SIMPLE_COMMANDS = [
    "open_app", "close_app", "shutdown", "restart",
    "volume_control", "git_push", "git_pull", "git_status",
    "git_fetch", "open_browser", "media_control", "run_terminal",
    "camera_on", "camera_off", "free_chat",
]

COMPLEX_COMMANDS = [
    "generate_prompt", "analyze_code", "summarize_file",
    "create_readme", "organize_files", "daily_summary",
]

# ── Action → Module Eşlemesi ─────────────────────────────────────────────────
ACTION_MODULE_MAP = {
    # Uygulama yönetimi
    "open_app":        "app_manager",
    "close_app":       "app_manager",

    # Sistem işlemleri
    "shutdown":        "system_control",
    "restart":         "system_control",
    "volume_control":  "system_control",

    # Git işlemleri
    "git_push":        "git_manager",
    "git_pull":        "git_manager",
    "git_status":      "git_manager",
    "git_fetch":       "git_manager",

    # Tarayıcı & medya
    "open_browser":    "browser_manager",
    "media_control":   "media_manager",

    # Jest ve Kamera Kontrolü
    "camera_on":       "gesture_manager",
    "camera_off":      "gesture_manager",

    # Terminal
    "run_terminal":    "terminal_manager",

    # Karmaşık / LLM-destekli işlemler
    "generate_prompt": "llm_tools",
    "analyze_code":    "llm_tools",
    "summarize_file":  "llm_tools",
    "create_readme":   "llm_tools",

    # Dosya & özet
    "organize_files":  "file_manager",
    "daily_summary":   "daily_manager",

    # Serbest sohbet
    "free_chat":       "free_chat",
}


def route(action: str) -> dict:
    """
    Verilen aksiyona göre kullanılacak modeli ve modülü belirler.

    Args:
        action: Brain'den gelen aksiyon adı (ör: "open_app", "git_push").

    Returns:
        dict: {"model": "simple"|"complex", "module": "<modül_adı>"|"unknown"}
    """
    # Model belirleme
    if action in SIMPLE_COMMANDS:
        model = "simple"
    elif action in COMPLEX_COMMANDS:
        model = "complex"
    else:
        model = "complex"  # Bilinmeyen aksiyonlar free_chat'e yönlendirilir
        logger.info(f"Tanınmayan aksiyon '{action}', free_chat modülüne yönlendiriliyor.")

    # Modül belirleme
    module = ACTION_MODULE_MAP.get(action, "free_chat")

    if module == "free_chat" and action not in ACTION_MODULE_MAP:
        logger.info(f"Tanınmayan aksiyon '{action}', free_chat modülüne yönlendiriliyor")

    result = {"model": model, "module": module}
    logger.info(f"Route: {action} → model={model}, module={module}")

    return result


def get_all_actions() -> dict:
    """Tüm desteklenen aksiyonları ve eşlemelerini döndürür."""
    return {
        action: {"model": "simple" if action in SIMPLE_COMMANDS else "complex", "module": module}
        for action, module in ACTION_MODULE_MAP.items()
    }


def is_known_action(action: str) -> bool:
    """Aksiyonun tanımlı olup olmadığını kontrol eder."""
    return action in ACTION_MODULE_MAP
