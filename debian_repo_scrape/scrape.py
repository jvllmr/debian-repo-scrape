from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urljoin

from debian_repo_scrape.navigation import ApacheBrowseNavigator, BaseNavigator
from debian_repo_scrape.utils import get_packages_files, get_release_file, get_suites
from debian_repo_scrape.verify import verify_hash_sums, verify_release_signatures

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Repository:
    url: str
    suites: list[Suite]

    @property
    def packages(self) -> list[Package]:
        return [p for s in self.suites for p in s.packages]


@dataclass(frozen=True)
class Suite:
    name: str
    components: list[Component]
    url: str
    architectures: list[str]
    date: str

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
    description: str | None
    maintainer: str
    section: str | None
    priority: str | None
    date: str
    architecture: str


def scrape_repo(
    repo_url: str | BaseNavigator, verify: bool = True, pub_key_file: str | None = None
) -> Repository:
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )

    if verify:
        verify_hash_sums(navigator)
        if pub_key_file is None:
            log.warning(
                """
                Verfying debian repsotiry integrity, but no public key was given.
                As a result the release signatures will not be verified.
                """
            )
        else:
            verify_release_signatures(navigator, pub_key_file)

    navigator["dists"]
    suites: list[Suite] = []
    for suite in get_suites(navigator):

        release_file = get_release_file(navigator.base_url, suite)
        components: list[Component] = []
        packages_map = get_packages_files(navigator.base_url, suite)
        for component, packages in packages_map.items():
            pkgs = [
                Package(
                    name=p["Package"],
                    version=p["version"],
                    url=urljoin(navigator.base_url, p["filename"]),
                    architecture=p["architecture"],
                    date=release_file["date"],
                    section=p.get("section"),
                    size=int(p["size"]),
                    sha256=p["sha256"],
                    sha1=p["sha1"],
                    md5=p["md5sum"],
                    priority=p.get("priority"),
                    maintainer=p["maintainer"],
                    description=p.get("description"),
                )
                for p in packages
            ]
            components.append(
                Component(
                    name=component,
                    packages=pkgs,
                    url=urljoin(navigator.base_url, f"dists/{suite}/{component}"),
                )
            )
        suites.append(
            Suite(
                name=suite,
                url=urljoin(navigator.base_url, f"{suite}"),
                components=components,
                architectures=release_file["architectures"].split(),
                date=release_file["date"],
            )
        )
    navigator.reset()
    return Repository(url=navigator.base_url, suites=suites)
