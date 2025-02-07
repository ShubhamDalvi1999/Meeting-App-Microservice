import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_verification_email(to_email: str, verification_token: str) -> bool:
    """Send verification email to user."""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            current_app.logger.error("SMTP credentials not configured")
            return False

        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email/{verification_token}"
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = "Verify your email address"

        html = f"""
        <html>
            <body>
                <h2>Welcome to Meeting App!</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <p>
                    <a href="{verification_url}">Verify Email Address</a>
                </p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
                <p>This link will expire in 24 hours.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return False 