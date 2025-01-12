import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_contact_email(name: str, email: str, phone: str, message: str, inquiry_type: str):
    sender_email = os.getenv("EMAIL")
    sender_password = os.getenv("PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    subject = f"New Contact Form Submission - {inquiry_type}"

    template_path = "templates/contact_email_template.html"

    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template: {e}")
        raise Exception("Failed to read email template.")

    html_content = html_content.replace('{{name}}', name)
    html_content = html_content.replace('{{email}}', email)
    html_content = html_content.replace('{{phone}}', phone)
    html_content = html_content.replace('{{inquiry_type}}', inquiry_type)
    html_content = html_content.replace('{{message}}', message)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Contact email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send contact email: {e}")
        raise Exception("Failed to send contact email.")


