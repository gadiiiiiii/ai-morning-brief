import anthropic
import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Config (set these as GitHub Secrets) ────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS     = os.environ["GMAIL_ADDRESS"]      # your gmail
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"] # gmail app password
RECIPIENT_EMAIL   = os.environ["RECIPIENT_EMAIL"]     # gmontiel@nd.edu
# ────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI newsletter curator for "AI Morning Brief", a daily digest for a graduate student studying AI and entrepreneurship.

Search the web for today's latest AI news (last 24-48 hours). Return ONLY a valid JSON object — no markdown, no backticks, no preamble. Use this exact structure:

{
  "headline": "one punchy sentence capturing today's AI landscape",
  "sub": "one sentence on the broader theme or mood in AI today",
  "top_stories": [
    {"title": "...", "summary": "2-3 sentence summary and why it matters", "source": "source name", "icon": "single emoji"},
    {"title": "...", "summary": "...", "source": "...", "icon": "..."},
    {"title": "...", "summary": "...", "source": "...", "icon": "..."}
  ],
  "tool_spotlight": {
    "name": "...",
    "description": "2-3 sentences on what it does and why it's worth knowing",
    "url": "url or empty string"
  },
  "term_of_the_day": {
    "term": "...",
    "definition": "clear 2-sentence explanation",
    "example": "one concrete real-world use case"
  },
  "quick_insight": "one thought-provoking sentence about where AI is heading"
}

Prioritize real news from the last 48 hours. Include exactly 3 top_stories."""


def generate_brief():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%A, %B %d, %Y")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"Generate today's AI Morning Brief for {today}. Search for the latest AI news, a noteworthy new tool, and pick an interesting AI term to teach me."
        }]
    )

    # Extract text from response (may include tool use blocks)
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    # Strip any accidental markdown fences
    clean = text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean), today


def build_html(nl, today):
    stories_html = ""
    for s in nl.get("top_stories", []):
        stories_html += f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid #f0f0f0;">
          <tr>
            <td width="42" valign="top">
              <div style="width:30px;height:30px;border-radius:6px;background:#f5f5f5;border:1px solid #e8e8e8;text-align:center;line-height:30px;font-size:14px;">{s.get('icon','📰')}</div>
            </td>
            <td valign="top">
              <p style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:14px;font-weight:600;margin:0 0 5px;line-height:1.35;">{s.get('title','')}</p>
              <p style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:13px;color:#555;line-height:1.55;margin:0 0 5px;">{s.get('summary','')}</p>
              <p style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;color:#aaa;margin:0;">{s.get('source','')}</p>
            </td>
          </tr>
        </table>"""

    tool = nl.get("tool_spotlight", {})
    term = nl.get("term_of_the_day", {})

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px 24px;color:#1a1a1a;background:#fff;">

  <div style="border-bottom:1px solid #e0e0e0;padding-bottom:16px;margin-bottom:24px;">
    <table width="100%"><tr>
      <td><span style="font-size:22px;font-weight:600;letter-spacing:-0.5px;">AI Morning Brief</span></td>
      <td align="right"><span style="font-size:12px;color:#888;">{today}</span></td>
    </tr></table>
    <p style="font-size:13px;color:#666;margin:4px 0 0;">Your daily digest — news, tools, and a concept to learn</p>
  </div>

  <div style="margin-bottom:28px;">
    <p style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#aaa;margin:0 0 10px;">Today's brief</p>
    <p style="font-size:18px;font-weight:600;line-height:1.4;margin:0 0 6px;">{nl.get('headline','')}</p>
    <p style="font-size:13px;color:#555;line-height:1.6;margin:0;">{nl.get('sub','')}</p>
  </div>

  <div style="border-top:1px solid #eee;padding-top:24px;margin-bottom:28px;">
    <p style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#aaa;margin:0 0 16px;">Top stories</p>
    {stories_html}
  </div>

  <div style="border-top:1px solid #eee;padding-top:24px;margin-bottom:28px;">
    <p style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#aaa;margin:0 0 12px;">Tool spotlight</p>
    <div style="background:#f9f9f9;border-radius:10px;border:1px solid #ebebeb;padding:16px 20px;">
      <p style="font-size:15px;font-weight:600;margin:0 0 6px;">{tool.get('name','')}</p>
      <p style="font-size:13px;color:#555;line-height:1.55;margin:0 0 8px;">{tool.get('description','')}</p>
      <p style="font-size:12px;color:#4a90d9;margin:0;">{tool.get('url','')}</p>
    </div>
  </div>

  <div style="border-top:1px solid #eee;padding-top:24px;margin-bottom:28px;">
    <p style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#aaa;margin:0 0 12px;">Term of the day</p>
    <div style="border-radius:10px;border:1px solid #ebebeb;padding:16px 20px;">
      <p style="font-size:16px;font-weight:600;margin:0 0 6px;">{term.get('term','')}</p>
      <p style="font-size:13px;color:#555;line-height:1.55;margin:0 0 12px;">{term.get('definition','')}</p>
      <p style="font-size:10px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#bbb;margin:0 0 6px;">In practice</p>
      <p style="font-size:13px;color:#555;line-height:1.55;margin:0;border-left:2px solid #ddd;padding-left:12px;">{term.get('example','')}</p>
    </div>
  </div>

  <div style="border-top:1px solid #eee;padding-top:24px;margin-bottom:32px;">
    <p style="font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#aaa;margin:0 0 12px;">Quick insight</p>
    <p style="font-size:15px;color:#1a1a1a;line-height:1.7;margin:0;font-style:italic;">{nl.get('quick_insight','')}</p>
  </div>

  <div style="border-top:1px solid #eee;padding-top:16px;">
    <p style="font-size:11px;color:#bbb;margin:0;text-align:center;">AI Morning Brief · Powered by Claude · Sent to {RECIPIENT_EMAIL}</p>
  </div>

</body>
</html>"""


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Brief sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    print("Generating brief...")
    nl, today = generate_brief()
    html = build_html(nl, today)
    subject = f"☕ AI Morning Brief — {today}"
    send_email(subject, html)
