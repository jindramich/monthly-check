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
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        context.add_cookies(_parse_cookie_header(cookie_header))
        page = context.new_page()
        _goto(page, PORTFOLIOS_URL)

        if "login.yahoo.com" in page.url or page.query_selector('a[href*="login.yahoo.com"]'):
            browser.close()
            sys.exit(
                "Yahoo did not accept the session cookies (redirected to login). "
                "Refresh the YAHOO_COOKIES secret with a fresh Cookie header."
            )

        # Collect links to individual portfolios/watchlists, then visit each
        # and pull the ticker symbols out of the holdings table.
        portfolio_links = {
            href
            for href in page.eval_on_selector_all(
                'a[href*="/portfolio/"]', "els => els.map(e => e.getAttribute('href'))"
            )
            if href and "/portfolio/" in href
        }

        symbols: list[str] = []
        if portfolio_links:
            for link in sorted(portfolio_links):
                url = link if link.startswith("http") else f"https://finance.yahoo.com{link}"
                _goto(page, url)
                symbols.extend(_extract_symbols(page))
        else:
            # Fallback: some layouts render holdings directly on /portfolios
            symbols.extend(_extract_symbols(page))

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
