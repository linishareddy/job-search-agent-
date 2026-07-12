#!/usr/bin/env python3
"""
LinkedIn Easy Apply — NO LLM, Playwright only.

Uses fixed saved_answers + question_map from JSON config.
Default is dry-run (fills form but does NOT click Submit).

Setup:
  pip install playwright python-dotenv
  playwright install chromium

Env (required for live run):
  LINKEDIN_EMAIL=
  LINKEDIN_PASSWORD=

Usage:
  python scripts/linkedin_easy_apply.py --config scripts/linkedin_apply_config.example.json --dry-run --headed
  python scripts/linkedin_easy_apply.py --config my_config.json --max-jobs 3 --headed
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("linkedin_easy_apply")

EASY_APPLY_SEARCH = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords={keywords}&location={location}&f_AL=true"
)


def _pause(min_s: float, max_s: float) -> None:
    time.sleep(random.uniform(min_s, max_s))


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def login(page, email: str, password: str) -> None:
    logger.info("Logging into LinkedIn…")
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    page.fill("#username", email)
    page.fill("#password", password)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle", timeout=60_000)
    if "checkpoint" in page.url or "challenge" in page.url:
        raise RuntimeError(
            "LinkedIn security checkpoint — complete verification in the browser, then retry."
        )
    if "feed" not in page.url and "jobs" not in page.url:
        logger.warning("Unexpected URL after login: %s", page.url)


def _fill_text_inputs(page, answers: dict, question_map: dict) -> None:
    for input_el in page.locator("input[type=text], input[type=email], input[type=tel], textarea").all():
        try:
            if not input_el.is_visible():
                continue
            label = _label_for(page, input_el)
            value = _match_answer(label, answers, question_map)
            if not value:
                continue
            tag = input_el.evaluate("el => el.tagName")
            current = input_el.input_value() if tag != "TEXTAREA" else input_el.inner_text()
            if current and current.strip():
                continue
            input_el.fill(str(value))
        except Exception:
            continue


def _label_for(page, input_el) -> str:
    el_id = input_el.get_attribute("id") or ""
    if el_id:
        label = page.locator(f"label[for='{el_id}']").first
        if label.count():
            return label.inner_text().strip().lower()
    aria = input_el.get_attribute("aria-label") or ""
    return aria.strip().lower()


def _match_answer(label: str, answers: dict, question_map: dict) -> str | None:
    if not label:
        return None
    for fragment, answer in question_map.items():
        if fragment.lower() in label:
            return answer
    aliases = {
        "first name": "first_name",
        "last name": "last_name",
        "email": "email",
        "phone": "phone",
        "mobile": "phone",
        "city": "city",
        "linkedin": "linkedin_url",
    }
    for alias, key in aliases.items():
        if alias in label:
            return answers.get(key)
    return None


def _answer_radio_selects(page, question_map: dict) -> None:
    """Pick radio / select options by matching question text to question_map."""
    for group in page.locator("fieldset, .jobs-easy-apply-form-section__grouping").all():
        try:
            if not group.is_visible():
                continue
            text = group.inner_text().lower()
            for fragment, answer in question_map.items():
                if fragment.lower() in text:
                    # Try radio with matching label
                    option = group.get_by_text(answer, exact=True)
                    if option.count():
                        option.first.click()
                        break
                    # Try contains match
                    option = group.locator(f"label:has-text('{answer}')")
                    if option.count():
                        option.first.click()
                        break
        except Exception:
            continue


def _upload_resume_if_needed(page, resume_path: Path | None) -> None:
    if not resume_path or not resume_path.exists():
        return
    file_input = page.locator("input[type=file]")
    if file_input.count():
        logger.info("Uploading resume: %s", resume_path)
        file_input.first.set_input_files(str(resume_path.resolve()))


def _click_easy_apply(page) -> bool:
    btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply')").first
    if not btn.count() or not btn.is_visible():
        return False
    btn.click()
    page.wait_for_selector(".jobs-easy-apply-modal, div[role=dialog]", timeout=15_000)
    return True


def _advance_modal(page, dry_run: bool) -> str:
    """
    Walk Easy Apply steps. Returns: submitted | review_ready | stuck | closed
    """
    for _ in range(12):
        if dry_run:
            submit = page.locator("button[aria-label='Submit application']")
            if submit.count() and submit.first.is_visible():
                logger.info("DRY RUN — would submit here (not clicking)")
                return "review_ready"

        if not dry_run:
            submit = page.locator("button[aria-label='Submit application']")
            if submit.count() and submit.first.is_visible():
                submit.first.click()
                _pause(2, 4)
                return "submitted"

        review = page.locator("button[aria-label='Review your application']")
        if review.count() and review.first.is_visible():
            review.first.click()
            _pause(1, 2)
            continue

        next_btn = page.locator(
            "button[aria-label='Continue to next step'], button[aria-label='Review']"
        )
        if next_btn.count() and next_btn.first.is_visible():
            next_btn.first.click()
            _pause(1, 2)
            continue

        dismiss = page.locator("button[aria-label='Dismiss']")
        if dismiss.count() and dismiss.first.is_visible():
            return "stuck"

        _pause(0.5, 1)

    return "stuck"


def apply_to_search_results(page, config: dict, dry_run: bool) -> list[dict]:
    search = config.get("search", {})
    limits = config.get("limits", {})
    answers = {**config.get("saved_answers", {})}
    question_map = config.get("question_map", {})
    resume_path = config.get("resume_path")
    resume = Path(resume_path) if resume_path else None

    keywords = search.get("keywords", "software engineer")
    location = search.get("location", "United States")
    max_jobs = limits.get("max_jobs", 1)
    delay_min = limits.get("delay_seconds_min", 3)
    delay_max = limits.get("delay_seconds_max", 7)

    url = EASY_APPLY_SEARCH.format(keywords=keywords.replace(" ", "%20"), location=location.replace(" ", "%20"))
    logger.info("Opening search: %s", url)
    page.goto(url, wait_until="domcontentloaded")
    _pause(2, 3)

    results: list[dict] = []
    cards = page.locator(".job-card-container, li.jobs-search-results__list-item")
    count = min(cards.count(), max_jobs)
    logger.info("Found %s job cards, processing %s", cards.count(), count)

    for i in range(count):
        card = cards.nth(i)
        try:
            title_el = card.locator(".job-card-list__title, a.job-card-container__link").first
            title = title_el.inner_text().strip() if title_el.count() else f"Job {i+1}"
            card.click()
            _pause(delay_min, delay_max)

            if not _click_easy_apply(page):
                results.append({"title": title, "status": "skipped", "reason": "no_easy_apply"})
                continue

            _fill_text_inputs(page, answers, question_map)
            _answer_radio_selects(page, question_map)
            _upload_resume_if_needed(page, resume)

            outcome = _advance_modal(page, dry_run=dry_run)
            results.append({"title": title, "status": outcome, "url": page.url})

            # Close modal if still open
            dismiss = page.locator("button[aria-label='Dismiss']")
            if dismiss.count() and dismiss.first.is_visible():
                dismiss.first.click()
                _pause(1, 2)
        except Exception as e:
            logger.error("Failed on job %s: %s", i + 1, e)
            results.append({"title": f"Job {i+1}", "status": "error", "reason": str(e)[:200]})

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="LinkedIn Easy Apply (no LLM)")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Do not submit (default)")
    parser.add_argument("--live", action="store_true", help="Actually submit applications")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--max-jobs", type=int, default=None)
    args = parser.parse_args()

    dry_run = not args.live
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Config not found: %s", config_path)
        return 1

    config = load_config(config_path)
    if args.max_jobs:
        config.setdefault("limits", {})["max_jobs"] = args.max_jobs

    email = os.getenv("LINKEDIN_EMAIL", "").strip()
    password = os.getenv("LINKEDIN_PASSWORD", "").strip()
    if not email or not password:
        logger.error("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env")
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Install Playwright: pip install playwright && playwright install chromium")
        return 1

    results: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            login(page, email, password)
            results = apply_to_search_results(page, config, dry_run=dry_run)
        finally:
            browser.close()

    print("\n=== Results ===")
    for r in results:
        print(f"  {r.get('title')}: {r.get('status')} {r.get('reason', '')}")

    ok = sum(1 for r in results if r.get("status") in ("submitted", "review_ready"))
    print(f"\n{ok}/{len(results)} reached submit/review step")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
