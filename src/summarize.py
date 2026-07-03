"""Turn the raw per-ticker data into a readable newsletter using Claude."""

import json

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are writing a monthly stock watchlist newsletter for a private investor.

You receive JSON with one entry per ticker: fundamentals, the 1-month price
change, and news items from the past month. Write the newsletter body as an
HTML fragment (no <html>/<head>/<body> tags — it will be embedded in an email
template).

For each ticker, produce a section with:
- A heading: company name (SYMBOL), the 1-month price change with an arrow
  (▲/▼), and current price.
- One short paragraph summarizing what actually mattered this month for this
  stock, synthesized from the news items. Focus on earnings, guidance, analyst
  actions, product/deal news, and anything explaining the price move. Skip
  clickbait and generic market commentary.
- Up to 3 bullet links to the most relevant articles: <a href="...">title</a>
  (publisher, date).
- If there was no meaningful news, say so in one sentence.

Order the sections by absolute size of the 1-month move (biggest movers
first). Start the newsletter with a 2-3 sentence overview of the whole
watchlist's month. Keep the tone factual and concise. Use only simple inline
HTML (h2, h3, p, ul, li, a, strong) so it renders well in email clients.
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
