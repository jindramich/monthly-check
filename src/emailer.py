"""Send the newsletter via Gmail SMTP (app password)."""

import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATE = """\
<div style="background:#ffffff;">
<div style="max-width:640px;margin:0 auto;
            font-family:Georgia,'Times New Roman',Times,serif;
            color:#111111;line-height:1.6;">
  <style>
    h1, h2 {{ font-weight: bold; }}
    a {{ color: #111111; }}
    .header {{
      background-color: #131313;
      background-image: radial-gradient(rgba(255,255,255,0.05) 18%, transparent 19%);
      background-size: 34px 34px;
      padding: 40px 32px 34px;
      margin-bottom: 8px;
    }}
    .header h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.15;
      letter-spacing: 0.2px;
      color: #f5f4ef;
    }}
    .header .sub {{
      margin: 10px 0 0;
      font-size: 12px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      color: #9a9a9a;
    }}
    .content {{ padding: 22px 32px 32px; }}
    .overview {{
      border-bottom: 1px solid #cccccc;
      padding: 18px 0 22px;
      margin-bottom: 4px;
      font-size: 15px;
    }}
    .overview p {{ margin: 0; }}
    .stock {{
      border-bottom: 1px solid #cccccc;
      padding: 26px 0;
    }}
    .stock h2 {{
      margin: 0 0 14px;
      font-size: 21px;
    }}
    table.fundamentals {{
      border-collapse: collapse;
      width: 100%;
      margin: 4px 0 18px;
      font-size: 14px;
    }}
    table.fundamentals td, table.fundamentals th {{
      border-bottom: 1px solid #e5e5e5;
      padding: 6px 4px;
      text-align: left;
    }}
    table.fundamentals td:first-child, table.fundamentals th:first-child {{
      color: #555555;
      width: 45%;
    }}
    table.fundamentals td:last-child {{ text-align: right; }}
    .positive, .negative {{ font-weight: 700; color: #111111; }}
    .stock p {{ font-size: 15px; margin: 0 0 14px; }}
    ul.sources {{
      list-style: none;
      margin: 0 0 16px;
      padding: 0;
      font-size: 12px;
      color: #666666;
    }}
    ul.sources li {{ padding: 3px 0; }}
    ul.sources li:before {{ content: "\\2014  "; }}
    p.yf-link {{ margin: 0; }}
    p.yf-link a {{
      display: inline-block;
      background-color: #131313;
      border-radius: 999px;
      color: #f5f4ef !important;
      text-decoration: none;
      font-size: 12px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 9px 18px;
    }}
    .footer {{
      font-size: 11px;
      color: #999999;
      padding-top: 18px;
    }}
  </style>
  <div class="header">
    <h1>Watchlist Monthly</h1>
    <p class="sub">{month} &middot; Monthly Check watchlist</p>
  </div>
  <div class="content">
    {body}
    <p class="footer">
      Generated automatically from your Yahoo Finance watchlist ({symbols}).
    </p>
  </div>
</div>
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
