"""Download verified Makerere University policy documents."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://policies.mak.ac.ug"
SOURCE_HOST = "policies.mak.ac.ug"
DEFAULT_OUTPUT_DIR = Path("knowledge/raw/mak-policies")
DEFAULT_REGISTER = Path("knowledge/source_register.json")
DEFAULT_MANIFEST = Path("knowledge/mak-policies-manifest.csv")
REQUEST_HEADERS = {"User-Agent": "MakerereStudentSupportAgent/1.0 (+policy-ingestion)"}
CATEGORY_PATH = re.compile(r"^/policy-category/[^/]+/?$")
POLICY_PATH = re.compile(r"^/policy/[^/]+/?$")
FILE_PREFIX = "/sites/default/files/"


def is_allowed_url(url: str, path_pattern: re.Pattern[str]) -> bool:
    """Return whether *url* is HTTPS on the exact host and expected path."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == SOURCE_HOST
        and parsed.port is None
        and not parsed.username
        and not parsed.password
        and bool(path_pattern.fullmatch(parsed.path))
    )


def is_allowed_file_url(url: str) -> bool:
    """Return whether *url* points into the official Drupal file tree."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    path = unquote(parsed.path)
    return (
        parsed.scheme == "https"
        and parsed.hostname == SOURCE_HOST
        and parsed.port is None
        and not parsed.username
        and not parsed.password
        and path.startswith(FILE_PREFIX)
        and path.removeprefix(FILE_PREFIX).strip("/")
        and ".." not in Path(path).parts
        and Path(path).name not in {"", ".", ".."}
    )


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "policy-document"


class MakPolicyDownloader:
    def __init__(
        self,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        register_path: Path = DEFAULT_REGISTER,
        manifest_path: Path = DEFAULT_MANIFEST,
        delay: float = 0.5,
        session: requests.Session | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.register_path = register_path
        self.manifest_path = manifest_path
        self.delay = delay
        self.session = session or requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

    def get_soup(self, url: str, timeout: int = 30) -> BeautifulSoup:
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def discover_category_urls(self) -> list[str]:
        soup = self.get_soup(f"{BASE_URL}/")
        categories = set()
        for anchor in soup.find_all("a", href=True):
            candidate = urljoin(BASE_URL, anchor["href"]).split("?", 1)[0]
            if is_allowed_url(candidate, CATEGORY_PATH):
                categories.add(candidate)
        return sorted(categories)

    def discover_policy_urls(self, category_url: str) -> list[str]:
        if not is_allowed_url(category_url, CATEGORY_PATH):
            raise ValueError(f"Disallowed category URL: {category_url}")
        policy_urls = set()
        seen_pages = set()
        next_url: str | None = category_url
        while next_url and next_url not in seen_pages:
            seen_pages.add(next_url)
            soup = self.get_soup(next_url)
            for anchor in soup.find_all("a", href=True):
                candidate = urljoin(BASE_URL, anchor["href"]).split("?", 1)[0]
                if is_allowed_url(candidate, POLICY_PATH):
                    policy_urls.add(candidate)
            next_link = soup.find("a", rel="next") or soup.find(
                "a", string=re.compile(r"next", re.IGNORECASE)
            )
            candidate = (
                urljoin(BASE_URL, next_link["href"]).split("?", 1)[0]
                if next_link and next_link.get("href")
                else None
            )
            next_url = candidate if candidate and is_allowed_url(candidate, CATEGORY_PATH) else None
            time.sleep(self.delay)
        return sorted(policy_urls)

    def discover_file(self, policy_url: str) -> tuple[str | None, str]:
        if not is_allowed_url(policy_url, POLICY_PATH):
            raise ValueError(f"Disallowed policy URL: {policy_url}")
        soup = self.get_soup(policy_url)
        title_tag = soup.find("h1")
        title = title_tag.get_text(" ", strip=True) if title_tag else policy_url
        for anchor in soup.find_all("a", href=True):
            candidate = urljoin(BASE_URL, anchor["href"]).split("?", 1)[0]
            if is_allowed_file_url(candidate):
                return candidate, title
        return None, title

    def download_file(self, file_url: str, destination: Path) -> None:
        if not is_allowed_file_url(file_url):
            raise ValueError(f"Disallowed file URL: {file_url}")
        response = self.session.get(file_url, timeout=60)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)

    def run(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        seen_policies = set()
        for category_url in self.discover_category_urls():
            category = urlparse(category_url).path.rstrip("/").split("/")[-1]
            for policy_url in self.discover_policy_urls(category_url):
                if policy_url in seen_policies:
                    continue
                seen_policies.add(policy_url)
                try:
                    file_url, title = self.discover_file(policy_url)
                    if not file_url:
                        continue
                    filename = safe_name(Path(urlparse(file_url).path).name)
                    destination = self.output_dir / category / filename
                    if not destination.exists():
                        self.download_file(file_url, destination)
                    rows.append(
                        {
                            "id": f"mak-policy-{len(rows) + 1:04d}",
                            "title": title,
                            "category": category,
                            "authority": "Makerere University",
                            "source_url": file_url,
                            "policy_page": policy_url,
                            "local_path": destination.as_posix(),
                        }
                    )
                except requests.RequestException as error:
                    print(f"Failed to fetch {policy_url}: {error}")
                time.sleep(self.delay)
        self.write_manifest(rows)
        self.update_register(rows)
        return rows

    def write_manifest(self, rows: list[dict[str, str]]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["id", "title", "category", "authority", "source_url", "policy_page", "local_path"]
        with self.manifest_path.open("w", newline="", encoding="utf-8") as manifest:
            writer = csv.DictWriter(manifest, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def update_register(self, rows: list[dict[str, str]]) -> None:
        register = json.loads(self.register_path.read_text(encoding="utf-8"))
        existing = [
            document
            for document in register.get("documents", [])
            if not document["id"].startswith("mak-policy-")
        ]
        register["documents"] = existing + rows
        self.register_path.write_text(
            json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()
    rows = MakPolicyDownloader(args.output_dir, args.register, args.manifest, args.delay).run()
    print(f"Downloaded or verified {len(rows)} Makerere policy documents.")


if __name__ == "__main__":
    main()