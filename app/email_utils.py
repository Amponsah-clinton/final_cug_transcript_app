from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

def send_email(to_email, subject, html_content):
    """Send an HTML email using Mailtrap SMTP."""
    try:
        msg = EmailMultiAlternatives(
            subject=subject or "",
            body="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content or "", "text/html")

        with get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        ) as conn:
            sent = conn.send_messages([msg])

        print(f"✅ Mailtrap SMTP OK: sent={sent}")
        return bool(sent)
    except Exception as e:
        print(f"❌ Mailtrap SMTP failed: {e}")
        return False
