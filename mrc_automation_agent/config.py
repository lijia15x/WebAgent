import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MrcConfig:
    sharepoint_site_url: str
    sharepoint_folder_template: str
    sharepoint_tenant: str
    sharepoint_client_id: str
    sharepoint_thumbprint: str
    sharepoint_certificate_path: str
    sharepoint_certificate_password: str
    mail_sender: str = ""
    header_search_rows: int = 10
    ppt_model: str = "gpt-5.5"

    @classmethod
    def from_env(cls) -> "MrcConfig":
        return cls(
            sharepoint_site_url=os.getenv("MRC_SHAREPOINT_SITE_URL", ""),
            sharepoint_folder_template=os.getenv("MRC_SHAREPOINT_FOLDER_TEMPLATE", ""),
            sharepoint_tenant=os.getenv("MRC_SHAREPOINT_TENANT", ""),
            sharepoint_client_id=os.getenv("MRC_SHAREPOINT_CLIENT_ID", ""),
            sharepoint_thumbprint=os.getenv("MRC_SHAREPOINT_THUMBPRINT", ""),
            sharepoint_certificate_path=os.getenv("MRC_SHAREPOINT_CERTIFICATE_PATH", ""),
            sharepoint_certificate_password=os.getenv(
                "MRC_SHAREPOINT_CERTIFICATE_PASSWORD", ""
            ),
            mail_sender=os.getenv("MRC_MAIL_SENDER", ""),
            header_search_rows=int(os.getenv("MRC_HEADER_SEARCH_ROWS", "10")),
            ppt_model=os.getenv("MRC_PPT_MODEL", "gpt-5.5"),
        )

    def require_sharepoint(self) -> None:
        self._require(
            {
                "MRC_SHAREPOINT_SITE_URL": self.sharepoint_site_url,
                "MRC_SHAREPOINT_FOLDER_TEMPLATE": self.sharepoint_folder_template,
                "MRC_SHAREPOINT_TENANT": self.sharepoint_tenant,
                "MRC_SHAREPOINT_CLIENT_ID": self.sharepoint_client_id,
                "MRC_SHAREPOINT_THUMBPRINT": self.sharepoint_thumbprint,
                "MRC_SHAREPOINT_CERTIFICATE_PATH": self.sharepoint_certificate_path,
                "MRC_SHAREPOINT_CERTIFICATE_PASSWORD": self.sharepoint_certificate_password,
            }
        )

    def require_mail(self) -> None:
        self.require_sharepoint()
        self._require({"MRC_MAIL_SENDER": self.mail_sender})

    @staticmethod
    def _require(values: dict[str, str]) -> None:
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing required configuration: " + ", ".join(missing)
            )