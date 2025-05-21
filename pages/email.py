import smtplib
from email.mime.text import MIMEText
import streamlit as st
def send_email(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your_email@gmail.com"
    password = "your_app_password"  # Tạo từ Google App Password

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Đã gửi email tới {to_email}")
    except Exception as e:
        st.error(f"Lỗi gửi email: {e}")
