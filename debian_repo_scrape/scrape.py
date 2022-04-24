from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from debian_repo_scrape.navigation import ApacheBrowseNavigator, BaseNavigator


@dataclass(frozen=True)
class Repository:
    url: str
    suites: list[Suite]


@dataclass(frozen=True)
class Suite:
    name: str
    components: list[Component]
    url: str
    architectures: list[str]
    date: datetime

    @property
    def packages(self) -> list[Package]:
        return [p for c in self.components for p in c.packages]


@dataclass(frozen=True)
class Component:
    name: str
    packages: list[Package]
    url: str


@dataclass(frozen=True)
class Package:
    name: str
    version: str
    url: str
    size: int
    sha256: str
    sha1: str
    md5: str
    description: str
    maintainer: str
    section: str
    priority: str


def scrape_repo(repoURL: str | BaseNavigator, verify: bool = True) -> Repository:
    navigator = ApacheBrowseNavigator(repoURL) if isinstance(repoURL, str) else repoURL
    navigator
