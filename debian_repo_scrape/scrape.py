from __future__ import annotations

import functools
import logging
import typing as t
from dataclasses import dataclass
from io import BufferedReader
from urllib.parse import urljoin

import typing_extensions as te
from debian.deb822 import Packages

from debian_repo_scrape.navigation import ApacheBrowseNavigator, BaseNavigator
from debian_repo_scrape.utils import (
    _get_file,
    get_packages_files,
    get_release_file,
    get_suites,
    get_suites_flat,
)
from debian_repo_scrape.verify import (
    VerificationModes,
    verify_hash_sums,
    verify_release_signatures,
)

log = logging.getLogger(__name__)


class BaseDataclass:
    @classmethod
    def from_dict(cls, dict_: dict[str, t.Any]):
        return cls(**dict_)  # pragma: no cover


@dataclass(frozen=True)
class FlatSuite(BaseDataclass):
    name: str
    url: str
    architectures: list[str]
    date: str
    package: Package


@dataclass(frozen=True)
class Suite(BaseDataclass):
    name: str
    components: list[Component]
    url: str
    architectures: list[str]
    date: str

    @property
    def packages(self) -> list[Package]:
        return [p for c in self.components for p in c.packages]


_S = t.TypeVar("_S", FlatSuite, Suite)


@dataclass(frozen=True)
class Repository(BaseDataclass, t.Generic[_S]):
    url: str
    suites: list[_S]

    @property
    def flat(self):
        return functools.reduce(
            lambda a, b: a and isinstance(b, FlatSuite), self.suites, True
        )

    @property
    def packages(self) -> list[Package]:
        return (
            [s.package for s in self.suites]  # type: ignore
            if self.flat
            else [p for s in self.suites for p in s.packages]  # type: ignore
        )


@dataclass(frozen=True)
class Component(BaseDataclass):
    name: str
    packages: list[Package]
    url: str


@dataclass(frozen=True)
class Package(BaseDataclass):
    name: str
    version: str
    url: str
    size: int
    sha256: str
    sha1: str
    md5: str
    description: str | None
    maintainer: str | None
    section: str | None
    priority: str | None
    date: str
    architecture: str
    description_md5: str | None
    phased_update_percentage: int | None


def scrape_repo(
    repo_url: str | BaseNavigator,
    pub_key_file: str | BufferedReader | bytes,
    verify: VerificationModes | str | te.Literal[False] = VerificationModes.STRICT,
) -> Repository[Suite]:
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )

    if verify:
        verify_release_signatures(navigator, pub_key_file)
        verify_hash_sums(navigator, verify)

    navigator.set_checkpoint()
    navigator.reset()
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
                    maintainer=p.get("maintainer"),
                    description=p.get("description"),
                    description_md5=p.get("description_md5"),
                    phased_update_percentage=p.get("Phased-Update-Percentage"),
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
    navigator.use_checkpoint()
    return Repository(url=navigator.base_url, suites=suites)


def scrape_flat_repo(
    repo_url: str | BaseNavigator,
    pub_key_file: str | BufferedReader | bytes,
    verify: VerificationModes | str | te.Literal[False] = VerificationModes.STRICT,
) -> Repository[FlatSuite]:
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )

    if verify:
        verify_release_signatures(navigator, pub_key_file, flat_repo=True)
        verify_hash_sums(navigator, verify, flat_repo=True)

    navigator.set_checkpoint()
    navigator.reset()
    suites: list[FlatSuite] = []

    for suite in get_suites_flat(navigator):
        release_file = get_release_file(navigator.base_url, suite, flat_repo=True)
        packages_file = Packages(
            _get_file(navigator.base_url, f"{suite}/Packages" if suite else "Packages")
        )
        package = Package(
            name=packages_file["Package"],
            version=packages_file["version"],
            url=urljoin(
                navigator.base_url,
                f'{suite}/{packages_file["filename"]}'
                if suite
                else packages_file["filename"],
            ),
            architecture=packages_file["architecture"],
            date=release_file["date"],
            section=packages_file.get("section"),
            size=int(packages_file["size"]),
            sha256=packages_file["sha256"],
            sha1=packages_file["sha1"],
            md5=packages_file["md5sum"],
            priority=packages_file.get("priority"),
            maintainer=packages_file.get("maintainer"),
            description=packages_file.get("description"),
            description_md5=packages_file.get("description_md5"),
            phased_update_percentage=packages_file.get("Phased-Update-Percentage"),
        )
        suites.append(
            FlatSuite(
                name=suite,
                url=urljoin(navigator.base_url, f"{suite}"),
                package=package,
                architectures=release_file["architectures"].split(),
                date=release_file["date"],
            )
        )

    navigator.use_checkpoint()
    return Repository(url=navigator.base_url, suites=suites)
