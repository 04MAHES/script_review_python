# import os
# import smtplib
# from email.message import EmailMessage
# from dotenv import load_dotenv
# load_dotenv()

# SMTP_HOST = os.getenv("SMTP_HOST")
# SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# SMTP_USER = os.getenv("SMTP_USER")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
# EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)


# def send_email(to_email: str, subject: str, body: str, attachment_bytes: bytes, filename: str):
#     print('send mail')
#     msg = EmailMessage()
#     msg["From"] = EMAIL_FROM
#     msg["To"] = to_email
#     msg["Subject"] = subject
#     msg.set_content(body)


#     msg.add_attachment(
#     attachment_bytes,
#     maintype="application",
#     subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#     filename=filename,
#     )


#     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_USER, SMTP_PASSWORD)
#         server.send_message(msg)

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_email(
    to_list: list,
    cc_list: list,
    bcc_list: list,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    filename: str
):
    print("send_email() function CALLED")

    # Build email
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(to_list)

    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    msg["Subject"] = subject
    msg.set_content(body)

    # Attachment
    msg.add_attachment(
        attachment_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )

    # All recipients
    recipients = to_list + cc_list + bcc_list

    # Send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg, to_addrs=recipients)
