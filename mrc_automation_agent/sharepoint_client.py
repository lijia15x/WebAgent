from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from .config import MrcConfig
from .models import WorkbookFile


def _excel_web_url(site_url: str, server_relative_url: str) -> str:
    file_url = urljoin(site_url, server_relative_url)
    parts = urlsplit(file_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["web"] = "1"
    return urlunsplit(parts._replace(query=urlencode(query)))


class SharePointClient:
    def __init__(self, config: MrcConfig) -> None:
        self._config = config

    def fetch_workbooks(self, cycle_code: str) -> list[WorkbookFile]:
        self._config.require_sharepoint()
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import pkcs12
        from office365.sharepoint.client_context import ClientContext

        with open(self._config.sharepoint_certificate_path, "rb") as stream:
            certificate_data = stream.read()
        private_key, _, _ = pkcs12.load_key_and_certificates(
            certificate_data,
            self._config.sharepoint_certificate_password.encode("utf-8"),
        )
        if private_key is None:
            raise ValueError("The configured PFX certificate has no private key")
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        context = ClientContext(self._config.sharepoint_site_url).with_client_certificate(
            tenant=self._config.sharepoint_tenant,
            client_id=self._config.sharepoint_client_id,
            thumbprint=self._config.sharepoint_thumbprint,
            private_key=private_key_pem,
        )
        folder_url = self._config.sharepoint_folder_template.format(
            cycle_code=cycle_code
        )
        files = context.web.get_folder_by_server_relative_url(folder_url).files.get()
        context.execute_query()

        workbooks: list[WorkbookFile] = []
        for file in files:
            name = str(file.properties.get("Name", ""))
            if not name.lower().endswith(".xlsx") or name.startswith("~$"):
                continue
            content = BytesIO()
            file.download(content).execute_query()
            source_url = _excel_web_url(
                self._config.sharepoint_site_url,
                str(file.properties.get("ServerRelativeUrl", "")),
            )
            workbooks.append(
                WorkbookFile(
                    name=name,
                    source_url=source_url,
                    content=content.getvalue(),
                    modified_time=str(file.properties.get("TimeLastModified", "")),
                )
            )
        return workbooks