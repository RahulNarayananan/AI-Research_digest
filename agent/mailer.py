"""
mailer.py — Builds a beautiful dark-mode HTML email and sends it via Gmail SMTP.

Environment variables required (set in .env):
    SENDER_EMAIL         — your Gmail address
    SENDER_APP_PASSWORD  — 16-char Gmail App Password
    RECIPIENT_EMAIL      — where the digest is delivered
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────────────────────
#  HTML EMAIL TEMPLATE
# ─────────────────────────────────────────────────────────────

def _build_html(papers_data: list[tuple[dict, dict[str, str]]], date_str: str) -> str:
    cards_html = ""
    
    for idx, (paper, sections) in enumerate(papers_data):
        rank = idx + 1
        authors_str = ", ".join(paper["authors"])
        if len(paper["authors"]) >= 5:
            authors_str += " et al."

        impact_pct   = round(paper.get("impact_score", 0) * 100)
        pub_date     = paper["published"][:10]
        cit_count    = paper["citation_count"]
        inf_count    = paper["influence_score"]
        gh_stars     = paper["github_stars"] if paper["github_stars"] else "—"

        section_html = ""
        section_data = [
            ("🎯", "Problem",      "problem",     "#ef4444"),
            ("💡", "Solution",     "solution",    "#10b981"),
            ("📊", "Results",      "results",     "#3b82f6"),
            ("⚠️", "Limitations", "limitations", "#f59e0b"),
            ("🚀", "Why It Matters","impact",     "#a855f7"),
        ]
        for icon, label, key, colour in section_data:
            content = sections.get(key) or "See the paper for details."
            section_html += f"""
            <tr>
              <td style="padding:8px 0;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0"
                       style="background:#1e1e2e;border-radius:10px;
                              border-left:3px solid {colour};overflow:hidden;">
                  <tr>
                    <td style="padding:14px 16px;">
                      <p style="margin:0 0 4px;font-size:10px;font-weight:700;
                                 text-transform:uppercase;letter-spacing:1px;color:#9ca3af;">
                        {icon}&nbsp; {label}
                      </p>
                      <p style="margin:0;font-size:13px;line-height:1.6;color:#d1d5db;">
                        {content}
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""

        # New reasoning box
        reasoning_html = ""
        if sections.get("why_it_matters"):
            reasoning_html = f"""
            <tr>
              <td style="padding:16px 0 8px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0"
                       style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);
                              border-radius:12px;">
                  <tr>
                    <td style="padding:14px 18px;">
                      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#c7d2fe;
                                 text-transform:uppercase;letter-spacing:0.8px;">
                        ✨ Why it matters
                      </p>
                      <p style="margin:0;font-size:13.5px;line-height:1.6;color:#e0e7ff;font-style:italic;">
                        &ldquo;{sections.get('why_it_matters')}&rdquo;
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""

        # Choose badge text
        badge_text = f"🔥 Rank #{rank} Impact" if rank == 1 else f"📈 Rank #{rank}"

        cards_html += f"""
                <!--– Paper card #{rank} –-->
                <tr>
                  <td style="padding:24px 0 0;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="background:linear-gradient(135deg,#1e1e2e,#1a1a28);
                                  border:1px solid rgba(99,102,241,0.2);
                                  border-radius:16px;overflow:hidden;">
                      <!-- Top gradient bar -->
                      <tr>
                        <td style="height:3px;
                                   background:linear-gradient(90deg,#6366f1,#a855f7,#ec4899);">
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:20px 24px 24px;">

                          <!-- Badge -->
                          <p style="margin:0 0 12px;display:inline-block;
                                    background:rgba(99,102,241,0.15);
                                    border:1px solid rgba(99,102,241,0.3);
                                    border-radius:8px;padding:4px 10px;
                                    font-size:10px;font-weight:700;color:#a5b4fc;
                                    text-transform:uppercase;letter-spacing:0.5px;">
                            {badge_text}
                          </p>

                          <!-- Title -->
                          <h2 style="margin:0 0 10px;font-size:18px;font-weight:600;
                                     color:#ffffff;line-height:1.4;">
                            {paper['title']}
                          </h2>

                          <!-- Meta -->
                          <p style="margin:0 0 16px;font-size:11px;color:#9ca3af;
                                    line-height:1.6;">
                            👤 {authors_str} &nbsp;·&nbsp; 📅 {pub_date}
                          </p>

                          <!-- CTA buttons -->
                          <table cellpadding="0" cellspacing="0" border="0"
                                 style="margin-bottom:12px;">
                            <tr>
                              <td style="padding-right:8px;">
                                <a href="{paper['arxiv_url']}"
                                   style="display:inline-block;padding:8px 18px;
                                          background:linear-gradient(135deg,#6366f1,#8b5cf6);
                                          color:#ffffff;text-decoration:none;
                                          border-radius:8px;font-size:12px;font-weight:500;">
                                  📄 View Paper
                                </a>
                              </td>
                              <td>
                                <a href="{paper['pdf_url']}"
                                   style="display:inline-block;padding:8px 18px;
                                          background:rgba(99,102,241,0.1);
                                          border:1px solid rgba(99,102,241,0.35);
                                          color:#a5b4fc;text-decoration:none;
                                          border-radius:8px;font-size:12px;font-weight:500;">
                                  ⬇️ PDF
                                </a>
                              </td>
                            </tr>
                          </table>

                          <!-- AI Reasoning -->
                          <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            {reasoning_html}
                          </table>

                          <!-- Technical breakdown spacer -->
                          <div style="height:12px;"></div>

                          <!-- Summary sections -->
                          <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            {section_html}
                          </table>

                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>AI Research Digest — {date_str}</title>
</head>
<body style="margin:0;padding:20px;background-color:#0a0a0f;
             font-family:'Segoe UI',Arial,sans-serif;color:#e8e8f0;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center">
        <table width="660" cellpadding="0" cellspacing="0" border="0"
               style="max-width:660px;">

          <!--=== HEADER ===-->
          <tr>
            <td style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
                       border-radius:20px 20px 0 0;padding:40px 40px 32px;
                       border-bottom:1px solid rgba(99,102,241,0.3);">

              <p style="margin:0 0 16px;display:inline-block;
                        background:rgba(99,102,241,0.15);
                        border:1px solid rgba(99,102,241,0.4);
                        border-radius:50px;padding:5px 16px;
                        font-size:11px;font-weight:700;color:#a5b4fc;
                        letter-spacing:0.8px;text-transform:uppercase;">
                🔬 Daily AI Research Digest
              </p>

              <h1 style="margin:0 0 8px;font-size:30px;font-weight:700;
                          color:#ffffff;line-height:1.2;">
                The Papers Making
                <span style="color:#a5b4fc;">
                  Waves Today
                </span>
              </h1>

              <p style="margin:0;font-size:13px;color:#9ca3af;">
                {date_str} &nbsp;·&nbsp; Curated from Hugging Face Trending AI Research
              </p>
            </td>
          </tr>

          <!--=== BODY ===-->
          <tr>
            <td style="background:#13131a;padding:0 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {cards_html}
                <!-- Spacing -->
                <tr><td style="height:32px;"></td></tr>
              </table>
            </td>
          </tr>

          <!--=== FOOTER ===-->
          <tr>
            <td style="background:#0f0f13;border-radius:0 0 20px 20px;
                       padding:24px 40px 32px;
                       border-top:1px solid rgba(255,255,255,0.06);
                       text-align:center;">
              <p style="margin:0 0 6px;font-size:14px;font-weight:600;color:#6366f1;">
                ⚛️ AI Research Digest
              </p>
              <p style="margin:0;font-size:11px;color:#4b5563;line-height:1.7;">
                Automatically generated by your personal AI research agent.<br>
                Trending papers curated from Hugging Face & Semantic Scholar<br>
                Summarised by Google Gemini · Delivered daily
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""
    return html



# ─────────────────────────────────────────────────────────────
#  PLAIN-TEXT FALLBACK
# ─────────────────────────────────────────────────────────────

def _build_plain(papers_data: list[tuple[dict, dict[str, str]]], date_str: str) -> str:
    divider = "─" * 60
    content = f"AI Research Digest — {date_str}\n{divider}\n\n"
    
    for idx, (paper, sections) in enumerate(papers_data):
        rank = idx + 1
        content += (
            f"PAPER #{rank}: {paper['title']}\n"
            f"Authors:   {', '.join(paper['authors'])}\n"
            f"View:      {paper['arxiv_url']}\n\n"
            f"WHY IT MATTERS: {sections.get('why_it_matters','')}\n"
            f"PROBLEM: {sections.get('problem','')}\n"
            f"SOLUTION: {sections.get('solution','')}\n"
            f"RESULTS: {sections.get('results','')}\n"
            f"IMPACT: {sections.get('impact','')}\n\n"
            f"{divider}\n\n"
        )
    
    content += "Delivered daily · AI Research Digest Agent\n"
    return content


# ─────────────────────────────────────────────────────────────
#  SEND EMAIL
# ─────────────────────────────────────────────────────────────

def send_email(papers_data: list[tuple[dict, dict[str, str]]], dry_run: bool = False) -> bool:
    """Compose and send (or preview) the digest email for multiple papers."""
    sender_email    = os.getenv("SENDER_EMAIL", "").strip()
    sender_password = os.getenv("SENDER_APP_PASSWORD", "").strip().replace(" ", "")
    
    # Parse comma-separated recipients
    recipients_raw  = os.getenv("RECIPIENT_EMAIL", "rahul.krishna010303@gmail.com")
    recipients      = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not sender_email or not sender_password:
        print(
            "[ERROR] SENDER_EMAIL or SENDER_APP_PASSWORD is missing.\n"
            "        Copy .env.example → .env and fill in your Gmail credentials."
        )
        return False

    if not papers_data:
        print("[ERROR] No paper data provided to send_email.")
        return False

    date_str = datetime.now().strftime("%A, %B %d, %Y")
    first_title = papers_data[0][0]["title"]
    subject = f"🔬 AI Research Digest: {first_title[:50]}… + {len(papers_data)-1} more"

    html_body  = _build_html(papers_data, date_str)
    plain_body = _build_plain(papers_data, date_str)

    # ── Dry-run: just save HTML preview ──────────────────────
    if dry_run:
        preview_path = "email_preview.html"
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        print(f"[DRY RUN] HTML preview saved to → {preview_path}")
        print(f"[DRY RUN] Subject : {subject}")
        print(f"[DRY RUN] To      : {', '.join(recipients)}")
        return True

    # ── Real send ─────────────────────────────────────────────
    msg                  = MIMEMultipart("alternative")
    msg["Subject"]       = subject
    msg["From"]          = f"AI Research Digest <{sender_email}>"
    msg["To"]            = ", ".join(recipients)
    msg["X-Mailer"]      = "AI-Research-Digest-Agent/1.0"

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print(f"[SUCCESS] Email delivered → {', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[ERROR] Gmail authentication failed.\n"
            "        Check SENDER_EMAIL and SENDER_APP_PASSWORD in your .env file.\n"
            "        Make sure you used an App Password (not your Gmail login password)."
        )
    except smtplib.SMTPException as exc:
        print(f"[ERROR] SMTP error: {exc}")
    except Exception as exc:
        print(f"[ERROR] Unexpected error while sending email: {exc}")

    return False

