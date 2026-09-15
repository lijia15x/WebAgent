from urllib.parse import quote

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from msal import ConfidentialClientApplication

from .config import MrcConfig
from .models import EmailDraft


class GraphEmailSender:
    def __init__(self, config: MrcConfig) -> None:
        self._config = config
        self._config.require_mail()
        with open(self._config.sharepoint_certificate_path, "rb") as stream:
            private_key, _, _ = pkcs12.load_key_and_certificates(
                stream.read(),
                self._config.sharepoint_certificate_password.encode("utf-8"),
            )
        if private_key is None:
            raise ValueError("The configured PFX certificate has no private key")
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        self._application = ConfidentialClientApplication(
            self._config.sharepoint_client_id,
            authority=f"https://login.microsoftonline.com/{self._config.sharepoint_tenant}",
            client_credential={
                "private_key": private_key_pem,
                "thumbprint": self._config.sharepoint_thumbprint,
            },
        )
        self._client = httpx.Client(timeout=30)

    def close(self) -> None:
        self._client.close()

    def send(self, draft: EmailDraft) -> None:
        token = self._application.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        access_token = token.get("access_token")
        if not access_token:
            raise RuntimeError(
                f"Microsoft Graph authentication failed: {token.get('error_description', 'unknown error')}"
            )
        response = self._client.post(
            "https://graph.microsoft.com/v1.0/users/"
            f"{quote(self._config.mail_sender)}/sendMail",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "message": {
                    "subject": draft.subject,
                    "body": {"contentType": "HTML", "content": draft.body_html},
                    "toRecipients": [
                        {"emailAddress": {"address": draft.owner_email}}
                    ],
                },
                "saveToSentItems": True,
            },
        )
        if not response.is_success:
            raise RuntimeError(
                f"Microsoft Graph sendMail failed ({response.status_code}): "
                f"{response.text[:2000]}"
            )