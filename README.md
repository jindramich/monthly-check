# monthly-check

Monthly fundamentals check with relevant news, sent straight to email.

Once a month a GitHub Action:

1. Logs into **Yahoo Finance** with your session cookies and reads the tickers
   from a single watchlist named **"monthly check"**, in the same order they
   appear there (headless browser — Yahoo has no official watchlist API).
2. Pulls each ticker's **fundamentals** (price, P/E, market cap, dividend
   yield, 52-week range, 1-month price change) and the **past month's news**
   via yfinance.
3. Has **Claude** write an in-depth digest per stock: what happened, why it
   plausibly moved the price, valuation context, and what to watch next
   month — with links to the key articles, in watchlist order.
4. **Emails** the newsletter to your inbox via Gmail.

## Setup

Add these repository secrets (GitHub → Settings → Secrets and variables →
Actions → New repository secret):

| Secret | What it is |
|---|---|
| `YAHOO_COOKIES` | Your Yahoo session Cookie header (see below) |
| `ANTHROPIC_API_KEY` | API key from [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_ADDRESS` | The Gmail address to send from (and to, unless `MAIL_TO` is set) |
| `GMAIL_APP_PASSWORD` | Gmail app password (see below) |
| `MAIL_TO` | *(optional)* Recipient address, defaults to `GMAIL_ADDRESS` |
| `YAHOO_WATCHLIST_NAME` | *(optional)* Only needed if your watchlist isn't named exactly `monthly check` |

### Creating the watchlist

In Yahoo Finance, create a watchlist named exactly **"monthly check"** and add
the tickers you want covered (e.g. 3 companies to start). Only tickers in that
one watchlist are pulled in — everything else in your Yahoo account is
ignored.

### Getting `YAHOO_COOKIES`

1. Log in to [finance.yahoo.com](https://finance.yahoo.com) in your browser.
2. Open DevTools (F12) → **Network** tab → reload the page.
3. Click the first request to `finance.yahoo.com` → **Headers** → find the
   **Cookie** request header.
4. Copy its entire value (a long `name=value; name=value; ...` string) into
   the `YAHOO_COOKIES` secret.

⚠️ These cookies are your login session — treat them like a password.
Yahoo session cookies typically stay valid for weeks to months, but they do
expire. If a run fails with a "redirected to login" error, repeat the steps
above to refresh the secret. Note this whole integration is unofficial and
can break if Yahoo changes their site.

### Getting a Gmail app password

1. Enable 2-step verification on your Google account.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Create an app password (e.g. named "monthly-check") and put the 16-character
   code in `GMAIL_APP_PASSWORD`.

## Running

- **Scheduled:** runs automatically on the first Friday of every month at
  10:00 Europe/Prague time (09:00 UTC), regardless of whether you open GitHub
  that day — this is a real cron trigger on GitHub's servers, not something
  that depends on you being active. Standard cron can't express "first Friday
  of the month" directly, so the workflow fires every Friday and the first
  step checks the date: if it's not within the 1st-7th of the month (i.e. not
  the first Friday), it skips the rest of the run. Note that 09:00 UTC is
  exactly 10:00 during CET (winter); during CEST (summer, roughly late March
  to late October) it lands at 11:00 local time instead, since GitHub Actions
  cron has no timezone/DST awareness.
- **Manually:** GitHub → Actions → *Monthly watchlist newsletter* → Run workflow.
  This always runs regardless of the date (the first-Friday check only
  applies to the scheduled trigger).

## Local run

```bash
pip install -r requirements.txt
playwright install chromium
export YAHOO_COOKIES='...' ANTHROPIC_API_KEY='...' GMAIL_ADDRESS='...' GMAIL_APP_PASSWORD='...'
python -m src.main
```
