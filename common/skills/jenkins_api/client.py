import os
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import httpx


class JenkinsError(RuntimeError):
    pass


@dataclass(frozen=True)
class JenkinsTarget:
    submitted_url: str
    status_url: str


def parse_jenkins_url(url: str) -> JenkinsTarget:
    submitted = urlsplit(url.strip())
    if submitted.scheme not in {"http", "https"} or not submitted.hostname:
        raise JenkinsError("Enter a valid HTTP or HTTPS Jenkins URL")
    if submitted.username or submitted.password:
        raise JenkinsError("The Jenkins URL must not contain a username or password")

    submitted_path = submitted.path.rstrip("/")
    if "/job/" not in submitted_path:
        raise JenkinsError("Enter a Jenkins job or build page URL")

    parts = [part for part in submitted_path.split("/") if part]
    is_build_url = bool(parts and parts[-1].isdigit())
    target_path = submitted_path if is_build_url else f"{submitted_path}/lastBuild"
    status_url = urlunsplit(
        (
            submitted.scheme,
            submitted.netloc,
            f"{target_path}/api/json",
            "tree=number,url,building,result,fullDisplayName",
            "",
        )
    )
    canonical_url = urlunsplit(
        (submitted.scheme, submitted.netloc, submitted_path + "/", "", "")
    )
    return JenkinsTarget(submitted_url=canonical_url, status_url=status_url)


class JenkinsClient:
    def __init__(self) -> None:
        username = os.environ.get("JENKINS_USERNAME")
        api_token = os.environ.get("JENKINS_API_TOKEN")
        if not username or not api_token:
            raise JenkinsError(
                "Missing JENKINS_USERNAME or JENKINS_API_TOKEN environment variable"
            )
        self.client = httpx.Client(
            auth=(username, api_token),
            follow_redirects=False,
            timeout=httpx.Timeout(20.0, connect=5.0),
        )

    def get_build_status(self, url: str) -> dict[str, object]:
        target = parse_jenkins_url(url)
        response = self.client.get(target.status_url)
        self._raise_for_status(response)
        data = response.json()
        return {
            "build_url": str(data["url"]).rstrip("/") + "/",
            "build_number": int(data["number"]),
            "building": bool(data["building"]),
            "build_result": data.get("result"),
        }

    def get_console_log(self, build_url: str) -> str:
        parse_jenkins_url(build_url)
        response = self.client.get(f"{build_url.rstrip('/')}/consoleText")
        self._raise_for_status(response)
        return response.content.decode("utf-8", errors="replace")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise JenkinsError("Jenkins authentication failed or the account lacks read access")
        if response.status_code == 404:
            raise JenkinsError("The specified Jenkins job or build was not found")
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise JenkinsError(f"Jenkins request failed: HTTP {response.status_code}") from exc