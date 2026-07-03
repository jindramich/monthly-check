"""Monthly watchlist newsletter: Yahoo watchlist -> news + fundamentals -> Claude summary -> email."""

from src.emailer import send_newsletter
from src.fetch_data import fetch_ticker_data
from src.fetch_watchlist import fetch_watchlist_symbols
from src.summarize import build_newsletter_html


def main() -> None:
    symbols = fetch_watchlist_symbols()
    print(f"Watchlist: {', '.join(symbols)}")

    ticker_data = [fetch_ticker_data(s) for s in symbols]
    for entry in ticker_data:
        print(f"{entry['symbol']}: {len(entry['news'])} news items, "
              f"1mo change {entry['month_change_pct']}%")

    body_html = build_newsletter_html(ticker_data)
    send_newsletter(body_html, symbols)


if __name__ == "__main__":
    main()
