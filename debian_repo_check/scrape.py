from dataclasses import dataclass


@dataclass(frozen=True)
class Repository:
    pass


@dataclass(frozen=True)
class Suite:
    pass


@dataclass(frozen=True)
class Package:
    pass


def scrape_repo(repoURL: str) -> Repository:
    pass
