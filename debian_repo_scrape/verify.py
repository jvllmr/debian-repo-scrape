from __future__ import annotations

import hashlib
import typing as t
from urllib.parse import urljoin

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
from debian_repo_scrape.utils import (
    _get_file,
    _get_file_abs,
    _get_release_file,
    get_release_file,
    get_suites,
)

HASH_FUNCTION_MAP: list[tuple[str, str, t.Type[HashInvalid]]] = [
    ("MD5Sum", "md5", MD5SumInvalid),
    ("SHA1", "sha1", SHA1Invalid),
    ("SHA256", "sha256", SHA256Invalid),
]


def verify_release_signatures(repo_url: str | BaseNavigator, pub_key_file: str):

    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    pgp_key, _ = PGPKey.from_file(pub_key_file)
    for suite in get_suites(navigator):

        release_file = _get_release_file(navigator.base_url, suite)

        release_sig = PGPSignature.from_blob(
            _get_file(navigator.base_url, f"dists/{suite}/Release.gpg")
        )

        pgp_key.verify(release_file, release_sig)
    navigator.reset()


def verify_hash_sums(repo_url: str | BaseNavigator):
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    navigator["dists"]
    for suite in get_suites(navigator):
        release_file = get_release_file(navigator.base_url, suite)
        navigator.set_checkpoint()
        navigator[suite]
        for key, hash_method, exc in HASH_FUNCTION_MAP:
            for file in release_file[key]:
                file_url = urljoin(navigator.current_url, file["name"])
                try:
                    file_content = _get_file_abs(file_url)
                    hashsum = hashlib.new(hash_method, file_content).hexdigest()
                    if not hashsum == file[key.lower()]:
                        raise exc(
                            file_url, urljoin(navigator.base_url, f"{suite}/Release")
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
                            deb_file_content = _get_file_abs(deb_file_url)

                            hashsum = hashlib.new(
                                hash_method_2, deb_file_content
                            ).hexdigest()
                            if not hashsum == packages_file[key_2.lower()]:
                                raise exc_2(deb_file_url, file_url)
        navigator.use_checkpoint()
    navigator.reset()


def verify_repo_integrity(repo_url: str | BaseNavigator, pub_key_file: str):
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    verify_release_signatures(navigator, pub_key_file)
    verify_hash_sums(navigator)
