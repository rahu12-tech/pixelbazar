import requests
import os
from django.conf import settings

def send_email_via_brevo(to_email, subject, content):
    """Send email using Brevo API instead of SMTP"""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY"),
        "content-type": "application/json",
    }
    data = {
        "sender": {"name": "PixelBazar", "email": "9a3106001@smtp-brevo.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<p>{content}</p>",
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 201, response.text
    except Exception as e:
        return False, str(e)