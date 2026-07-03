"""Fetch fundamentals and the past month's news for each ticker via yfinance."""

from datetime import datetime, timedelta, timezone

import yfinance as yf

NEWS_WINDOW_DAYS = 31
MAX_NEWS_PER_TICKER = 15


def _parse_news_item(item: dict) -> dict | None:
    # yfinance >= 0.2.50 nests everything under "content"; older versions are flat.
    content = item.get("content", item)

    title = content.get("title")
    if not title:
        return None

    published = None
    if content.get("pubDate"):
        published = datetime.fromisoformat(content["pubDate"].replace("Z", "+00:00"))
    elif item.get("providerPublishTime"):
        published = datetime.fromtimestamp(item["providerPublishTime"], tz=timezone.utc)

    link = None
    canonical = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
    if isinstance(canonical, dict):
        link = canonical.get("url")
    link = link or item.get("link")

    publisher = None
    provider = content.get("provider") or {}
    if isinstance(provider, dict):
        publisher = provider.get("displayName")
    publisher = publisher or item.get("publisher")

    return {
        "title": title,
        "summary": content.get("summary") or content.get("description") or "",
        "published": published.isoformat() if published else None,
        "_published_dt": published,
        "link": link,
        "publisher": publisher,
    }


def fetch_ticker_data(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    cutoff = datetime.now(timezone.utc) - timedelta(days=NEWS_WINDOW_DAYS)

    news = []
    try:
        for raw in ticker.news or []:
            parsed = _parse_news_item(raw)
            if parsed is None:
                continue
            dt = parsed.pop("_published_dt")
            if dt is None or dt >= cutoff:
                news.append(parsed)
    except Exception as exc:  # noqa: BLE001 - one bad ticker shouldn't kill the run
        print(f"[warn] news fetch failed for {symbol}: {exc}")
    news = news[:MAX_NEWS_PER_TICKER]

    fundamentals = {}
    try:
        info = ticker.info or {}
        fundamentals = {
            "name": info.get("shortName") or info.get("longName") or symbol,
            "currency": info.get("currency"),
            "price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("trailingPegRatio") or info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] fundamentals fetch failed for {symbol}: {exc}")

    month_change_pct = None
    try:
        hist = ticker.history(period="1mo")["Close"].dropna()
        if len(hist) >= 2:
            month_change_pct = round((hist.iloc[-1] / hist.iloc[0] - 1) * 100, 2)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] history fetch failed for {symbol}: {exc}")

    return {
        "symbol": symbol,
        "yahoo_finance_url": f"https://finance.yahoo.com/quote/{symbol}",
        "fundamentals": fundamentals,
        "month_change_pct": month_change_pct,
        "news": news,
    }
