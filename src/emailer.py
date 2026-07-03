"""Send the newsletter via Gmail SMTP (app password)."""

import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATE = """\
<div style="background:#f2f1ec;padding:24px 12px;">
<div style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e3e1d8;
            border-radius:10px;overflow:hidden;
            font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
            color:#22242b;line-height:1.6;">
  <style>
    h1, h2 {{ font-family: Georgia, 'Times New Roman', serif; }}
    a {{ color: #0f5f8c; }}
    .header {{
      background: linear-gradient(135deg, #12324f, #0f5f8c);
      color: #ffffff;
      padding: 28px 32px;
    }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .header .sub {{ margin: 6px 0 0; font-size: 13px; color: #cfe3ef; }}
    .content {{ padding: 8px 32px 32px; }}
    .overview {{
      background: #f5f8fa;
      border-left: 4px solid #0f5f8c;
      padding: 14px 18px;
      margin: 20px 0 28px;
      font-size: 15px;
    }}
    .overview p {{ margin: 0; }}
    .stock {{
      border: 1px solid #e3e1d8;
      border-radius: 8px;
      padding: 20px 24px 22px;
      margin-bottom: 24px;
      background: #fffefb;
    }}
    .stock h2 {{
      margin: 0 0 12px;
      font-size: 19px;
      border-bottom: 2px solid #eae7da;
      padding-bottom: 8px;
    }}
    table.fundamentals {{
      border-collapse: collapse;
      width: 100%;
      margin: 4px 0 18px;
      font-size: 14px;
    }}
    table.fundamentals tr:nth-child(even) {{ background: #f7f6f1; }}
    table.fundamentals td, table.fundamentals th {{
      border: 1px solid #eae7da;
      padding: 6px 12px;
      text-align: left;
    }}
    table.fundamentals td:first-child, table.fundamentals th:first-child {{
      color: #555;
      width: 45%;
    }}
    .positive {{ color: #146c2e; font-weight: 600; }}
    .negative {{ color: #b3261e; font-weight: 600; }}
    .stock p {{ font-size: 15px; margin: 0 0 14px; }}
    ul.sources {{
      list-style: none;
      margin: 0 0 16px;
      padding: 0;
      font-size: 13px;
      color: #666;
    }}
    ul.sources li {{
      padding: 4px 0;
      border-top: 1px solid #f0efe8;
    }}
    p.yf-link {{ margin: 0; }}
    p.yf-link a {{
      display: inline-block;
      background: #0f5f8c;
      color: #ffffff !important;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
      padding: 8px 16px;
      border-radius: 20px;
    }}
    .footer {{
      font-size: 12px;
      color: #888;
      border-top: 1px solid #eae7da;
      padding-top: 14px;
      margin-top: 8px;
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
