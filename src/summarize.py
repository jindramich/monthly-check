"""Turn the raw per-ticker data into a readable newsletter using Claude."""

import json

import anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """\
You are writing a monthly stock watchlist newsletter for a private investor.

You receive a JSON array with one entry per ticker: fundamentals, the
1-month price change, a Yahoo Finance URL, and news items from the past
month. Write the newsletter body as an HTML fragment (no <html>/<head>/<body>
tags — it will be embedded in an email template).

**Preserve the input order.** The array is already in the user's watchlist
order — present the tickers in that exact same order, top to bottom. Do not
reorder by price move, alphabetically, or any other criterion.

For each ticker, produce a section in this exact structure, in this order:

1. **Heading**: company name (SYMBOL).

2. **Fundamentals overview** — a compact two-column HTML table (or a short
   list if a table doesn't fit the data) with these rows, in this order:
   - 1-Month Price Change (as a %, with an ▲/▼ arrow)
   - P/E (TTM)
   - P/E (Forward)
   - PEG Ratio
   - Dividend Yield
   - Market Cap
   Use "N/A" for any field that's missing or null in the data — never invent
   a number.

3. **News overview** — one or two paragraphs of flowing prose (NOT a bulleted
   list) that synthesize all the important news from the past month for this
   stock into a single concise narrative: earnings, guidance, analyst
   actions, product/deal news, and anything else that mattered. You may
   mention notable sentiment shifts if the news supports it, but don't force
   it if there's nothing there. Use specific figures from the news (revenue,
   percentages, dollar amounts, dates) rather than vague language like
   "strong results." If there was no meaningful news this month, say so in
   one plain sentence instead of padding.

4. **Sources** — a bullet list below the news overview, linking to the
   specific articles the overview above drew from: <a href="...">title</a>
   (publisher, date). Only include sources actually referenced in the prose,
   don't pad with irrelevant links.

5. **Yahoo Finance link** — a single line linking to the ticker's Yahoo
   Finance page, using the `yahoo_finance_url` field from the data, e.g.
   <a href="...">View SYMBOL on Yahoo Finance</a>.

Start the newsletter with a 2-3 sentence overview of the whole watchlist's
month, before the per-ticker sections. Keep the tone factual and precise —
this is meant to be read closely, not skimmed. Use only simple inline HTML
(h2, h3, p, table, tr, td, th, ul, li, a, strong) so it renders well in email
clients.
"""


def build_newsletter_html(ticker_data: list[dict]) -> str:
    client = anthropic.Anthropic()

    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is this month's watchlist data:\n\n"
                    + json.dumps(ticker_data, ensure_ascii=False, indent=1)
                ),
            }
        ],
    ) as stream:
        message = stream.get_final_message()

    return "".join(block.text for block in message.content if block.type == "text")
