import smtplib
import ssl
from email.message import EmailMessage

from .config import MrcConfig
from .models import EmailDraft


MRC_CC_EMAIL = "sys_DHE_AI_ASSISTANT@intel.com"


class SmtpEmailSender:
    def __init__(self, config: MrcConfig) -> None:
        self._config = config
        self._config.require_mail()
        self._client = smtplib.SMTP(
            self._config.smtp_server,
            self._config.smtp_port,
            timeout=30,
        )
        try:
            self._client.ehlo()
            self._client.starttls(context=ssl.create_default_context())
            self._client.ehlo()
            self._client.login(
                self._config.smtp_sender_email,
                self._config.smtp_sender_password,
            )
        except Exception:
            self._client.close()
            raise

    def close(self) -> None:
        try:
            self._client.quit()
        except smtplib.SMTPServerDisconnected:
            pass

    def send(self, draft: EmailDraft) -> None:
        message = EmailMessage()
        message["From"] = self._config.smtp_sender_email
        message["To"] = draft.owner_email
        message["Cc"] = MRC_CC_EMAIL
        message["Subject"] = draft.subject
        message.set_content(draft.body_html, subtype="html", charset="utf-8")
        self._client.send_message(message)