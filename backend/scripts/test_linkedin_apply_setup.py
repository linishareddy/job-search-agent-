#!/usr/bin/env python3
"""Verify Playwright is installed and can load LinkedIn login page (no credentials needed)."""
import sys


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("FAIL: playwright not installed")
        print("  pip install playwright")
        print("  playwright install chromium")
        return 1

    print("OK: playwright import")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30_000)
        title = page.title()
        has_username = page.locator("#username").count() > 0
        browser.close()

    if "LinkedIn" in title and has_username:
        print(f"OK: LinkedIn login page loaded (title={title!r})")
        print("\nNext steps:")
        print("  1. Copy scripts/linkedin_apply_config.example.json → linkedin_apply_config.json")
        print("  2. Add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to backend/.env")
        print("  3. Run: python scripts/linkedin_easy_apply.py --config linkedin_apply_config.json --headed --dry-run")
        return 0

    print(f"WARN: unexpected page title={title!r}, username field={has_username}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
