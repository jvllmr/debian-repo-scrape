from __future__ import annotations

from urllib.parse import urljoin

import requests
from debian.deb822 import Packages, Release

from debian_repo_scrape.exc import FileRequestError


def _get_file(base_url: str, rel_path: str) -> bytes:
    if not base_url.endswith("/"):
        base_url += "/"
    url = urljoin(base_url, rel_path)
    resp = requests.get(url)
    if resp.status_code != 200:
        raise FileRequestError(url, resp.status_code)
    return resp.content


def _get_release_file(repoURL: str, suite: str):
    return _get_file(repoURL, f"dists/{suite}/Release")


def get_release_file(repoURL: str, suite: str):
    return Release(_get_release_file(repoURL, suite).split(b"\n"))


def _get_packages_files(repoURL: str, suite: str) -> dict[str, list[bytes]]:
    if not repoURL.endswith("/"):
        repoURL += "/"
    release_file = get_release_file(repoURL, suite)
    packages = {}
    for key in ("SHA256", "SHA1", "MD5Sum"):
        val = release_file.get(key, None)
        if val:
            for file in val:
                filename = file["name"]

                if not filename.endswith("Packages"):
                    continue
                component_name = filename.split("/")[0]
                comp_packages = packages.get(component_name, None)
                packages_file = _get_file(repoURL, f"dists/{suite}/{filename}")
                if not packages_file:
                    continue
                if comp_packages is not None:
                    packages[component_name].append(packages_file)
                else:
                    packages[component_name] = [packages_file]
            break

    return packages


def get_packages_files(repoURL: str, suite: str) -> dict[str, list[Packages]]:
    return {
        component: [Packages(p.split(b"\n")) for p in ps]
        for component, ps in _get_packages_files(repoURL, suite).items()
    }
