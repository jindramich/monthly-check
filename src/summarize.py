"""Turn the raw per-ticker data into a readable newsletter using Claude."""

import json

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are writing a monthly stock watchlist newsletter for a private investor
who wants real depth, not a surface-level recap.

You receive a JSON array with one entry per ticker: fundamentals, the
1-month price change, a Yahoo Finance URL, and news items from the past
month. Write the newsletter body as an HTML fragment (no <html>/<head>/<body>
tags — it will be embedded in an email template that already provides page
styling, so focus on content and semantic markup rather than inline styles).

**Preserve the input order.** The array is already in the user's watchlist
order — present the tickers in that exact same order, top to bottom. Do not
reorder by price move, alphabetically, or any other criterion.

For each ticker, wrap the whole section in <div class="stock"> and produce
this exact structure, in this order:

1. **Heading** (<h2>): company name (SYMBOL).

2. **Fundamentals overview** — a <table class="fundamentals"> with these rows,
   in this order:
   - 1-Month Price Change — as a %, wrapped in <span class="positive"> if
     it's a gain or <span class="negative"> if it's a loss, with an ▲/▼
     arrow, e.g. <span class="positive">▲ 4.2%</span>
   - P/E (TTM)
   - P/E (Forward)
   - PEG Ratio
   - Dividend Yield
   - Market Cap
   Use "N/A" for any field that's missing or null in the data — never invent
   a number.

3. **News overview** — thorough flowing prose (NOT a bulleted list) that goes
   genuinely deep on this stock's past month — treat every distinct news item
   in the data as worth a mention, not just the single dominant narrative.
   Don't compress multiple separate developments into one vague sentence;
   walk through each one. Cover, to the extent the news supports it:
   - Every specific thing that happened, individually: earnings results vs.
     estimates, guidance changes, each analyst action with the analyst/firm
     name and old/new rating or price target, insider buying/selling with
     dollar amounts, product or partnership announcements (name the products,
     partners, and deals), litigation, management changes, shareholder
     meeting outcomes, macro/sector events that touched this name — anything
     present in the news data.
   - Why it plausibly moved the price the way it did this month — connect
     the news explicitly to the 1-month % change rather than just listing
     events next to it.
   - Valuation context: given the P/E, PEG, and dividend yield above, does
     the move look justified by fundamentals, or like sentiment/momentum
     running ahead of (or behind) the numbers? Say so explicitly, and
     mention analyst price targets vs. the current price if the data
     includes them.
   - Notable sentiment shifts over the month, if the news supports it (e.g.
     analysts turning more cautious/bullish, changing narrative) — don't
     force this if there's nothing there.
   - What to watch next month: an upcoming earnings date if inferable from
     the data, pending catalysts, or open questions the news raised.
   Use specific figures and named entities from the news (company and
   analyst/firm names, revenue numbers, percentages, dollar amounts, exact
   dates) instead of vague language like "strong results" or "mixed news."
   Every claim should trace back to something in the provided data — if the
   news doesn't support a claim, don't make it. Length should follow from
   how much the news actually supports, not a fixed target — a ticker with
   many distinct developments should get a longer, more thorough writeup
   than one with little news. If there was no meaningful news this month,
   say so plainly in one sentence rather than padding with generic
   commentary.

4. **Sources** — a <ul class="sources"> below the news overview, linking to
   the specific articles the overview above actually drew from:
   <li><a href="...">title</a> — publisher, date</li>. Only include sources
   actually referenced in the prose, don't pad with irrelevant links.

5. **Yahoo Finance link** — a single line: <p class="yf-link"><a href="...">
   View SYMBOL on Yahoo Finance</a></p>, using the ticker's `yahoo_finance_url`
   field.

Before the per-ticker sections, add a <div class="overview"> with a 3-4
sentence overview of the whole watchlist's month — what stood out, which
names moved most and in what direction, and any theme connecting them if one
genuinely exists (don't invent a connection that isn't there).

Keep the tone factual, specific, and analytical — this is meant to be read
closely, not skimmed. Use only this HTML vocabulary: div (with the classes
named above), h2, p, table, tr, td, th, ul, li, a, strong, span (with the
classes named above). Do not add your own inline style attributes or extra
classes — the email template's stylesheet already handles appearance for the
classes listed above.
"""


def build_newsletter_html(ticker_data: list[dict]) -> str:
    client = anthropic.Anthropic()

    with client.messages.stream(
        model=MODEL,
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
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
