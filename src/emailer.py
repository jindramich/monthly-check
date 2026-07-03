"""Send the newsletter via Gmail SMTP (app password)."""

import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATE = """\
<div style="max-width:680px;margin:0 auto;font-family:Georgia,serif;color:#222;line-height:1.5;">
  <style>
    table {{ border-collapse: collapse; margin: 12px 0; }}
    td, th {{ border: 1px solid #ccc; padding: 4px 10px; text-align: left; }}
  </style>
  <h1 style="border-bottom:2px solid #222;padding-bottom:8px;">Watchlist Monthly &mdash; {month}</h1>
  {body}
  <p style="margin-top:32px;font-size:12px;color:#888;border-top:1px solid #ddd;padding-top:8px;">
    Generated automatically from your Yahoo Finance watchlist ({symbols}).
  </p>
</div>
"""


def send_newsletter(body_html: str, symbols: list[str]) -> None:
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("MAIL_TO") or sender

    if not sender or not password:
        sys.exit("GMAIL_ADDRESS / GMAIL_APP_PASSWORD are not set. See README.")

    month = date.today().strftime("%B %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Watchlist Monthly — {month}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(
        MIMEText(
            TEMPLATE.format(month=month, body=body_html, symbols=", ".join(symbols)),
            "html",
            "utf-8",
        )
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    print(f"Newsletter sent to {recipient}")
