from __future__ import annotations
from dataclasses import dataclass

from debian_repo_scrape.navigation import ApacheBrowseNavigator, BaseNavigator


@dataclass(frozen=True)
class Repository:
    pass


@dataclass(frozen=True)
class Suite:
    pass


@dataclass(frozen=True)
class Package:
    pass


def scrape_repo(
    repoURL: str, verify: bool = True, navigator: BaseNavigator | None = None
) -> Repository:
    pass
