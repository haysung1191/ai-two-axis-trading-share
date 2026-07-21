from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as s:
        s.ehlo()
        if use_tls:
            s.starttls()
            s.ehlo()
        if user:
            s.login(user, password)
        s.send_message(msg)

