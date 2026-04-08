import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv("SENDER_EMAIL", "").strip()
sender_password = os.getenv("SENDER_APP_PASSWORD", "").strip().replace(" ", "")

print(f"Testing login for: {sender_email}")
print(f"Password length: {len(sender_password)}")

if not sender_email or not sender_password:
    print("Missing email or password in .env")
    exit(1)

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # server.set_debuglevel(1)
        server.login(sender_email, sender_password)
        print("✅ SUCCESS! Gmail authentication worked.")
except Exception as e:
    print(f"❌ FAILED: {e}")
