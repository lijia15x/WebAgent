import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)


class DatabaseConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("WEBAGENT_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("WEBAGENT_DB_PORT", "3306")),
            name=os.getenv("WEBAGENT_DB_NAME", "webagent"),
            user=os.getenv("WEBAGENT_DB_USER", ""),
            password=os.getenv("WEBAGENT_DB_PASSWORD", ""),
        )

    def require(self) -> None:
        missing = []
        if not self.user:
            missing.append("WEBAGENT_DB_USER")
        if not self.password:
            missing.append("WEBAGENT_DB_PASSWORD")
        if missing:
            raise DatabaseConfigurationError(
                "Missing required database configuration: " + ", ".join(missing)
            )


class MySqlDatabase:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig.from_env()

    @contextmanager
    def connection(self) -> Iterator[Any]:
        self.config.require()
        import mysql.connector

        connection = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.name,
            user=self.config.user,
            password=self.config.password,
            charset="utf8mb4",
            connection_timeout=10,
        )
        try:
            yield connection
        finally:
            connection.close()
