from __future__ import annotations

import bz2
import gzip
import hashlib
import logging
import lzma
import os
import re
import typing as t
from enum import Enum
from io import BufferedReader
from urllib.parse import urljoin

from debian.deb822 import Packages
from pgpy import PGPKey, PGPMessage, PGPSignature

from debian_repo_scrape.exc import (
    FileError,
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
    clear_response_cache,
    get_release_file,
    get_suites,
    get_suites_flat,
)

log = logging.getLogger(__name__)

HASH_FUNCTION_MAP: list[tuple[str, str, t.Type[HashInvalid]]] = [
    ("MD5Sum", "md5", MD5SumInvalid),
    ("SHA1", "sha1", SHA1Invalid),
    ("SHA256", "sha256", SHA256Invalid),
]
PACKAGES_FILE_REGEX = r"Packages(\..+)?"
IMPORTANT_FILES_REGEX = (PACKAGES_FILE_REGEX, r".+\.deb", r"Sources.gz")


class VerificationModes(str, Enum):
    STRICT = "strict"
    RAISE_IMPORTANT_ONLY = "raise_important_only"
    IGNORE_MISSING = "ignore_missing"
    IGNORE_MISSING_NON_IMPORTANT = "ignore_missing_non_important"
    VERIFY_IMPORTANT_ONLY = "verify_important_only"
    VERIFY_IMPORTANT_ONLY_IGNORE_MISSING = "verify_important_only_ignore_missing"


VERIFY_IMPORTANT_ONLY = (
    VerificationModes.VERIFY_IMPORTANT_ONLY,
    VerificationModes.VERIFY_IMPORTANT_ONLY_IGNORE_MISSING,
)

IGNORE_MISSING = (
    VerificationModes.IGNORE_MISSING,
    VerificationModes.IGNORE_MISSING_NON_IMPORTANT,
    VerificationModes.VERIFY_IMPORTANT_ONLY_IGNORE_MISSING,
)

RAISE_EXCEPTION = (VerificationModes.STRICT, VerificationModes.VERIFY_IMPORTANT_ONLY)
RAISE_EXCEPTION_IMPORTANT_FILE = (
    VerificationModes.RAISE_IMPORTANT_ONLY,
    VerificationModes.IGNORE_MISSING_NON_IMPORTANT,
)


def verify_release_signatures(
    repo_url: str | BaseNavigator,
    pub_key_file: str | BufferedReader | bytes,
    flat_repo: bool = False,
):

    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    navigator.set_checkpoint()
    navigator.reset()

    if isinstance(pub_key_file, BufferedReader):
        pgp_key, _ = PGPKey.from_blob(pub_key_file.read())
    elif isinstance(pub_key_file, str):
        pgp_key, _ = PGPKey.from_file(pub_key_file)
    elif isinstance(pub_key_file, bytes):
        pgp_key, _ = PGPKey.from_blob(pub_key_file)
    else:
        raise TypeError(
            f"{type(pub_key_file)} is not a valid type for public key input"
        )

    suites = get_suites_flat(navigator) if flat_repo else get_suites(navigator)

    for suite in suites:

        release_file = _get_release_file(navigator.base_url, suite, flat_repo)

        if not flat_repo:
            base_path = f"dists/{suite}/"
        elif suite:
            base_path = f"{suite}/"
        else:
            base_path = ""

        release_sig = PGPSignature.from_blob(
            _get_file(navigator.base_url, f"{base_path}Release.gpg")
        )

        pgp_key.verify(release_file, release_sig)

        in_release_file = _get_file(navigator.base_url, f"{base_path}InRelease")
        pgp_message = PGPMessage.from_blob(in_release_file)
        pgp_key.verify(pgp_message)

    navigator.use_checkpoint()
    clear_response_cache()


def __check_important(file: str) -> bool:
    for pattern in IMPORTANT_FILES_REGEX:
        if re.match(pattern, os.path.basename(file)):
            return True
    return False


def __check_reraise(mode: str, e: FileError):
    if (
        mode in RAISE_EXCEPTION
        or (mode in RAISE_EXCEPTION_IMPORTANT_FILE and __check_important(e.file))
        or (isinstance(e, HashInvalid) and mode in IGNORE_MISSING)
    ):
        raise e

    elif (
        isinstance(e, FileRequestError) and mode not in IGNORE_MISSING
    ) or not isinstance(e, FileRequestError):
        log.warning(e)


def verify_hash_sums(
    repo_url: str | BaseNavigator,
    mode: VerificationModes | str = VerificationModes.STRICT,
    flat_repo: bool = False,
):
    if isinstance(mode, VerificationModes):
        mode = mode.value
    if mode not in [e.value for e in VerificationModes]:
        raise ValueError(f"{mode} is not a valid verification mode")

    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    processed_urls: list[str] = []
    navigator.set_checkpoint()
    navigator.reset()
    if flat_repo:
        suites = get_suites_flat(navigator)
    else:
        suites = get_suites(navigator)
        navigator["dists"]
    for suite in suites:
        release_file = get_release_file(navigator.base_url, suite, flat_repo=flat_repo)
        release_file_url = urljoin(navigator.base_url, f"{suite}/Release")

        navigator.set_checkpoint()
        if suite:
            navigator[suite]
        for key, hash_method, exc in HASH_FUNCTION_MAP:
            hashed_files = release_file[key]
            if mode in VERIFY_IMPORTANT_ONLY:
                hashed_files = [
                    file for file in hashed_files if __check_important(file["name"])
                ]
            for file in hashed_files:
                file_url = urljoin(navigator.current_url, file["name"])
                try:
                    file_content = _get_file_abs(file_url)
                    hashsum = hashlib.new(hash_method, file_content).hexdigest()
                    if not hashsum == file[key.lower()]:
                        __check_reraise(mode, exc(file_url, release_file_url))
                    if release_file.get("Acquire-by-Hash") == "yes":
                        by_hash_url = urljoin(file_url, f"by-hash/{key}/{hashsum}")

                        by_hash_file = _get_file_abs(by_hash_url)
                        assert (
                            by_hash_file == file_content
                        ), f"Could not acquire {file_url} by hash"
                except FileRequestError as e:
                    e.file_mentioned_by = release_file_url
                    __check_reraise(mode, e)
                    if mode in IGNORE_MISSING:
                        continue

                packages_match = re.match(
                    PACKAGES_FILE_REGEX, os.path.basename(file_url)
                )
                if packages_match and file_url not in processed_urls:
                    processed_urls.append(file_url)
                    if packages_match.group(1) == ".gz":
                        file_content = gzip.decompress(file_content)
                    elif packages_match.group(1) in (".xz", ".lzma"):
                        file_content = lzma.decompress(file_content)  # pragma: no cover
                    elif packages_match.group(1) == ".bz2":
                        file_content = bz2.decompress(file_content)  # pragma: no cover

                    packages_file = Packages(file_content.split(b"\n"))

                    if packages_file.keys():
                        packages_file_fn = packages_file["Filename"]
                        if mode in VERIFY_IMPORTANT_ONLY and not __check_important(
                            packages_file_fn
                        ):
                            continue  # pragma: no cover
                        for key_2, hash_method_2, exc_2 in HASH_FUNCTION_MAP:
                            deb_file_url = urljoin(navigator.base_url, packages_file_fn)

                            try:
                                deb_file_content = _get_file_abs(deb_file_url)
                            except FileRequestError as e:
                                e.file_mentioned_by = file_url
                                __check_reraise(mode, e)
                                if mode in IGNORE_MISSING:
                                    continue

                            hashsum = hashlib.new(
                                hash_method_2, deb_file_content
                            ).hexdigest()
                            if not hashsum == packages_file[key_2.lower()]:
                                __check_reraise(mode, exc_2(deb_file_url, file_url))
        navigator.use_checkpoint()
    navigator.use_checkpoint()
    clear_response_cache()


def verify_repo_integrity(
    repo_url: str | BaseNavigator,
    pub_key_file: str | BufferedReader | bytes,
    mode: VerificationModes = VerificationModes.STRICT,
    flat_repo: bool = False,
):
    navigator = (
        ApacheBrowseNavigator(repo_url) if isinstance(repo_url, str) else repo_url
    )
    verify_release_signatures(navigator, pub_key_file, flat_repo)
    verify_hash_sums(navigator, mode, flat_repo)
