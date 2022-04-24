from __future__ import annotations

import hashlib
import typing as t
from urllib.parse import urljoin

import requests
from debian.deb822 import Packages
from pgpy import PGPKey, PGPSignature

from debian_repo_scrape.exc import (
    FileRequestError,
    HashInvalid,
    MD5SumInvalid,
    SHA1Invalid,
    SHA256Invalid,
)
from debian_repo_scrape.navigation import ApacheBrowseNavigator, BaseNavigator
from debian_repo_scrape.utils import _get_file, _get_release_file, get_release_file

HASH_FUNCTION_MAP: list[tuple[str, t.Callable[[bytes], t.Any], HashInvalid]] = [
    ("MD5Sum", hashlib.md5, MD5SumInvalid),
    ("SHA1", hashlib.sha1, SHA1Invalid),
    ("SHA256", hashlib.sha256, SHA256Invalid),
]


def verify_release_signatures(repoURL: str | BaseNavigator, pub_key_file: str):

    navigator = ApacheBrowseNavigator(repoURL) if isinstance(repoURL, str) else repoURL
    pgp_key, _ = PGPKey.from_file(pub_key_file)
    navigator["dists"]
    for suite in navigator.directions:
        if suite == "..":
            continue

        release_file = _get_release_file(navigator.base_url, suite)

        release_sig = PGPSignature.from_blob(
            _get_file(navigator.base_url, f"dists/{suite}/Release.gpg")
        )

        pgp_key.verify(release_file, release_sig)
    navigator.reset()


def _verify_file_hash(
    url: str, expected: str, method: t.Callable, exc: t.Type[HashInvalid] = HashInvalid
):
    resp = requests.get(url, stream=True)
    if resp.status_code != 200:
        raise FileRequestError(url, resp.status_code)

    hashsum = method(resp.content).hexdigest()
    if not hashsum == expected:
        raise exc(url)

    return resp.content


def verify_hash_sums(repoURL: str | BaseNavigator):
    navigator = ApacheBrowseNavigator(repoURL) if isinstance(repoURL, str) else repoURL
    navigator["dists"]
    for suite in navigator.directions:
        if suite == "..":
            continue

        release_file = get_release_file(navigator.base_url, suite)
        navigator[suite]
        for key, hash_method, exc in HASH_FUNCTION_MAP:
            for file in release_file[key]:
                file_url = urljoin(navigator.current_url, file["name"])
                try:
                    file_content = _verify_file_hash(
                        file_url, file[key.lower()], hash_method, exc
                    )
                except FileRequestError:
                    if file_url.endswith("Packages"):
                        raise
                if file_url.endswith("Packages"):
                    packages_file = Packages(file_content.split(b"\n"))
                    if packages_file.keys():
                        for key_2, hash_method_2, exc_2 in HASH_FUNCTION_MAP:
                            deb_file_url = urljoin(
                                navigator.base_url, packages_file["Filename"]
                            )
                            _verify_file_hash(
                                deb_file_url, packages_file[key_2], hash_method_2, exc_2
                            )
        navigator[".."]

    navigator.reset()


def verify_repo_integrity(repoURL: str | BaseNavigator, pub_key_file: str):
    navigator = ApacheBrowseNavigator(repoURL) if isinstance(repoURL, str) else repoURL
    verify_release_signatures(navigator, pub_key_file)
    verify_hash_sums(navigator)
