"""Fetch watchlist tickers from the logged-in Yahoo Finance account.

Yahoo has no official watchlist API, so this drives a headless browser with
the user's session cookies (YAHOO_COOKIES env var — the raw Cookie header
copied from a logged-in browser session).
"""

import os
import re
import sys

from playwright.sync_api import sync_playwright

PORTFOLIOS_URL = "https://finance.yahoo.com/portfolios"
QUOTE_RE = re.compile(r"/quote/([A-Za-z0-9^.\-=]+)")

# Non-ticker slugs that can appear in /quote/ links (nav, promos)
IGNORED_SYMBOLS = {"quote"}

# Only pull tickers from the one Yahoo watchlist with this name (case-insensitive).
# Override with the YAHOO_WATCHLIST_NAME env var if your watchlist is named differently.
DEFAULT_WATCHLIST_NAME = "monthly check"


def _parse_cookie_header(header: str) -> list[dict]:
    cookies = []
    for part in header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append(
            {
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".yahoo.com",
                "path": "/",
            }
        )
    return cookies


def _goto(page, url: str) -> None:
    # Yahoo Finance never reaches "networkidle" (continuous background
    # polling for quotes/ads/analytics), so wait only for the DOM, then
    # give the page a bit of extra time to hydrate its client-side content.
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    try:
        page.wait_for_selector('a[href*="/quote/"], a[href*="/portfolio/"]', timeout=15_000)
    except Exception:
        pass  # fall through; caller decides if the resulting page has useful links


def _is_logged_in(page) -> bool:
    # Yahoo doesn't always redirect an unauthenticated request to
    # login.yahoo.com -- it can just serve the logged-out page with a
    # "Sign in" prompt and HTTP 200. That's the more reliable signal.
    return page.query_selector('a:has-text("Sign in"), button:has-text("Sign in")') is None


def _find_watchlist_link(page, watchlist_name: str) -> str | None:
    entries = page.eval_on_selector_all(
        'a[href*="/portfolio/"]',
        "els => els.map(e => ({href: e.getAttribute('href'), "
        "text: (e.textContent || '').trim()}))",
    )
    target = watchlist_name.strip().lower()

    # Exact name match first, then fall back to a substring match in case
    # Yahoo renders extra text (e.g. a share count) alongside the name.
    for entry in entries:
        if (entry.get("text") or "").strip().lower() == target:
            return entry.get("href")
    for entry in entries:
        if target in (entry.get("text") or "").strip().lower():
            return entry.get("href")
    return None


def _extract_symbols(page) -> list[str]:
    symbols = []
    for href in page.eval_on_selector_all(
        'a[href*="/quote/"]', "els => els.map(e => e.getAttribute('href'))"
    ):
        m = QUOTE_RE.search(href or "")
        if m and m.group(1) not in IGNORED_SYMBOLS:
            symbols.append(m.group(1))
    return symbols


def fetch_watchlist_symbols() -> list[str]:
    cookie_header = os.environ.get("YAHOO_COOKIES", "").strip()
    if not cookie_header:
        sys.exit("YAHOO_COOKIES is not set. See README for how to provide it.")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            # Reduce headless/automation fingerprint signals that trigger
            # bot-detection challenges even with valid session cookies.
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        context.add_cookies(_parse_cookie_header(cookie_header))
        page = context.new_page()
        _goto(page, PORTFOLIOS_URL)

        if "login.yahoo.com" in page.url or not _is_logged_in(page):
            print(f"[debug] not logged in. Final URL: {page.url}")
            print(f"[debug] page title: {page.title()!r}")
            debug_path = "yahoo_debug.png"
            try:
                page.screenshot(path=debug_path, full_page=True)
                print(f"[debug] saved screenshot to {debug_path}")
            except Exception as exc:  # noqa: BLE001
                print(f"[debug] screenshot failed: {exc}")
            browser.close()
            sys.exit(
                "Yahoo is treating this session as logged out (either redirected "
                "to login, or served a page with a 'Sign in' prompt). This can "
                "happen even with a Cookie header copied from a real browser if "
                "you weren't actually signed in at the time, the cookies expired, "
                "or Yahoo's bot detection flagged the request. Log into Yahoo "
                "Finance, confirm you see your account avatar/name (not a 'Sign "
                "in' button) before copying the Cookie header, and refresh the "
                "YAHOO_COOKIES secret. Check the yahoo_debug.png artifact if this "
                "keeps happening."
            )

        watchlist_name = os.environ.get("YAHOO_WATCHLIST_NAME") or DEFAULT_WATCHLIST_NAME
        link = _find_watchlist_link(page, watchlist_name)
        if not link:
            browser.close()
            sys.exit(
                f'No watchlist named "{watchlist_name}" was found on your Yahoo '
                "portfolios page. Create a watchlist with that exact name in Yahoo "
                "Finance, or set the YAHOO_WATCHLIST_NAME secret to match the name "
                "you're using."
            )

        url = link if link.startswith("http") else f"https://finance.yahoo.com{link}"
        _goto(page, url)
        symbols = _extract_symbols(page)

        browser.close()

    # Dedupe, preserve order
    seen = set()
    unique = [s for s in symbols if not (s in seen or seen.add(s))]
    if not unique:
        sys.exit(
            "No tickers found in the Yahoo watchlist. Either the watchlist is "
            "empty or Yahoo changed its page structure."
        )
    return unique


if __name__ == "__main__":
    print("\n".join(fetch_watchlist_symbols()))
