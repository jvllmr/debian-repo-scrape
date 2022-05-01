from __future__ import annotations

import functools
import logging
import re
import typing as t
from urllib.parse import urljoin

import requests
from debian.deb822 import Packages, Release

from debian_repo_scrape.exc import FileRequestError, NoDistsPath

if t.TYPE_CHECKING:
    from debian_repo_scrape.navigation import BaseNavigator

log = logging.getLogger(__name__)


@functools.lru_cache(None)
def __get_response(url: str):
    return requests.get(url, allow_redirects=True)


def _get_response(url: str):

    return __get_response(url.strip("/"))


def clear_response_cache():
    return __get_response.cache_clear()


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


def _get_release_file(repo_url: str, suite: str, flat_repo: bool = False):
    if not flat_repo:
        path = f"dists/{suite}/Release"
    elif suite:
        path = f"{suite}/Release"
    else:
        path = "Release"

    return _get_file(repo_url, path)


def get_release_file(repo_url: str, suite: str, flat_repo: bool = False):
    return Release(_get_release_file(repo_url, suite, flat_repo).split(b"\n"))


def _get_packages_files(repo_url: str, suite: str) -> dict[str, list[bytes]]:
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

        if re.match(r"binary-.+|sources", suite):
            log.warning(
                f'Searching for suites lead to "{suite}" directory. If the folder is not part of a suite name, this usually means that the Release file for that suite is missing.'  # noqa: E501
            )
        navigator.set_checkpoint()
        old_url = navigator.current_url
        navigator[suite]
        if navigator.current_url == old_url:
            continue

        if "Release" not in navigator.directions:
            suites.extend(f"{suite}/{subsuite}" for subsuite in __get_suites(navigator))
        else:
            suites.append(suite)

        navigator.use_checkpoint()

    return suites


def get_suites(navigator: BaseNavigator) -> list[str]:
    navigator.set_checkpoint()
    navigator.reset()

    try:
        navigator["dists"]
    except ValueError:  # pragma: no cover
        raise NoDistsPath

    suites = __get_suites(navigator)

    navigator.use_checkpoint()
    return suites


def get_suites_flat(navigator: BaseNavigator) -> list[str]:
    navigator.set_checkpoint()
    navigator.reset()

    if "Release" in navigator.directions:
        suites = [""] + __get_suites(navigator)
    else:
        suites = __get_suites(navigator)

    navigator.use_checkpoint()
    return suites
