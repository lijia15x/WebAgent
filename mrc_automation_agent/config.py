import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MrcConfig:
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str
    sharepoint_site_url: str
    sharepoint_folder_template: str
    sharepoint_tenant: str
    sharepoint_client_id: str
    sharepoint_thumbprint: str
    sharepoint_certificate_path: str
    sharepoint_certificate_password: str
    header_search_rows: int = 10

    @classmethod
    def from_env(cls) -> "MrcConfig":
        return cls(
            database_host=os.getenv("MRC_DB_HOST", "127.0.0.1"),
            database_port=int(os.getenv("MRC_DB_PORT", "3306")),
            database_name=os.getenv("MRC_DB_NAME", "webagent"),
            database_user=os.getenv("MRC_DB_USER", ""),
            database_password=os.getenv("MRC_DB_PASSWORD", ""),
            sharepoint_site_url=os.getenv("MRC_SHAREPOINT_SITE_URL", ""),
            sharepoint_folder_template=os.getenv("MRC_SHAREPOINT_FOLDER_TEMPLATE", ""),
            sharepoint_tenant=os.getenv("MRC_SHAREPOINT_TENANT", ""),
            sharepoint_client_id=os.getenv("MRC_SHAREPOINT_CLIENT_ID", ""),
            sharepoint_thumbprint=os.getenv("MRC_SHAREPOINT_THUMBPRINT", ""),
            sharepoint_certificate_path=os.getenv("MRC_SHAREPOINT_CERTIFICATE_PATH", ""),
            sharepoint_certificate_password=os.getenv(
                "MRC_SHAREPOINT_CERTIFICATE_PASSWORD", ""
            ),
            header_search_rows=int(os.getenv("MRC_HEADER_SEARCH_ROWS", "10")),
        )

    def require_database(self) -> None:
        self._require(
            {
                "MRC_DB_USER": self.database_user,
                "MRC_DB_PASSWORD": self.database_password,
            }
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

    @staticmethod
    def _require(values: dict[str, str]) -> None:
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing required configuration: " + ", ".join(missing)
            )