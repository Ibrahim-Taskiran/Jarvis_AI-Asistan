"""
test_router.py - Router modulu dogrulama testi
Farkli action'larla route() fonksiyonunu test eder.
"""

import sys
import io

# Windows konsol encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from core.router import route, is_known_action

def main():
    print("=" * 65)
    print("  JARVIS Router Modulu - Test")
    print("=" * 65)

    test_cases = [
        ("open_app",        "simple",  "app_manager"),
        ("git_push",        "simple",  "git_manager"),
        ("shutdown",        "simple",  "system_control"),
        ("summarize_file",  "complex", "llm_tools"),
        ("daily_summary",   "complex", "daily_manager"),
        ("hack_nasa",       "simple",  "unknown"),       # bilinmeyen aksiyon
    ]

    passed = 0
    failed = 0

    print(f"\n{'Action':<20} {'Model':<10} {'Module':<20} {'Sonuc'}")
    print("-" * 65)

    for action, expected_model, expected_module in test_cases:
        result = route(action)
        model_ok = result["model"] == expected_model
        module_ok = result["module"] == expected_module
        status = "PASS" if (model_ok and module_ok) else "FAIL"

        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"{action:<20} {result['model']:<10} {result['module']:<20} [{status}]")

    # is_known_action testi
    print(f"\n{'=' * 65}")
    print("  is_known_action() Testi")
    print("-" * 65)

    known_tests = [
        ("open_app", True),
        ("git_pull", True),
        ("hack_nasa", False),
    ]

    for action, expected in known_tests:
        actual = is_known_action(action)
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        print(f"  is_known_action('{action}') = {actual:<6} [{status}]")

    print(f"\n{'=' * 65}")
    print(f"  Sonuc: {passed} PASSED, {failed} FAILED")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
