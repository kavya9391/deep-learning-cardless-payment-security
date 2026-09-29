import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SecureFinancialTransactions.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Testing email configuration...")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

try:
    send_mail(
        'Test Email - OTP System',
        'This is a test email to verify SMTP configuration is working.',
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print("\nSUCCESS: Email sent successfully!")
except Exception as e:
    print(f"\nERROR: Email failed: {str(e)}")
    print("\nPossible solutions:")
    print("1. Check if your Gmail App Password is correct")
    print("2. Verify 2-Step Verification is enabled on your Google account")
    print("3. Check your firewall/antivirus settings")
    print("4. Try disabling Windows Firewall temporarily")
    print("5. Check if port 587 is blocked by your network")
