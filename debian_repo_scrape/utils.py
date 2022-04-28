from __future__ import annotations

import functools
import typing as t
from urllib.parse import urljoin

import requests
from debian.deb822 import Packages, Release

from debian_repo_scrape.exc import FileRequestError, NoDistsPath

if t.TYPE_CHECKING:
    from debian_repo_scrape.navigation import BaseNavigator


@functools.lru_cache(None)
def _get_response(url: str):
    return requests.get(url, allow_redirects=True)


def _get_file_abs(
    url: str,
):
    resp = _get_response(url)
    if resp.status_code != 200:
        raise FileRequestError(url, resp.status_code)
    return resp.content


def _get_file(base_url: str, rel_path: str) -> bytes:
    if not base_url.endswith("/"):
        base_url += "/"
    url = urljoin(base_url, rel_path)

    return _get_file_abs(url)


def _get_release_file(repo_url: str, suite: str):
    return _get_file(repo_url, f"dists/{suite}/Release")


def get_release_file(repo_url: str, suite: str):
    return Release(_get_release_file(repo_url, suite).split(b"\n"))


def _get_packages_files(repo_url: str, suite: str) -> dict[str, list[bytes]]:
    if not repo_url.endswith("/"):
        repo_url += "/"
    release_file = get_release_file(repo_url, suite)
    packages: dict[str, list[bytes]] = {}
    for key in ("SHA256", "SHA1", "MD5Sum"):
        val = release_file.get(key, None)
        if val:
            for file in val:
                filename = file["name"]

                if not filename.endswith("Packages"):
                    continue
                component_name = filename.split("/")[0]
                comp_packages = packages.get(component_name, None)
                packages_file = _get_file(repo_url, f"dists/{suite}/{filename}")
                if not packages_file:
                    continue
                if comp_packages is not None:
                    packages[component_name].append(packages_file)
                else:
                    packages[component_name] = [packages_file]
            break

    return packages


def get_packages_files(repo_url: str, suite: str) -> dict[str, list[Packages]]:
    return {
        component: [Packages(p.split(b"\n")) for p in ps]
        for component, ps in _get_packages_files(repo_url, suite).items()
    }


def __get_suites(navigator: BaseNavigator) -> list[str]:
    suites: list[str] = []
    for suite in navigator.directions:
        if suite == "..":
            continue
        navigator[suite]
        if "Release" not in navigator.directions:
            for subsuite in __get_suites(navigator):
                suites.append(f"{suite}/{subsuite}")
        else:
            suites.append(suite)

        navigator[".."]

    return suites


def get_suites(navigator: BaseNavigator) -> list[str]:
    navigator.set_checkpoint()
    navigator.reset()

    try:
        navigator["dists"]
    except ValueError:
        raise NoDistsPath()

    suites = __get_suites(navigator)

    navigator.use_checkpoint()
    return suites
