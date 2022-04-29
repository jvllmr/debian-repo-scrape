from __future__ import annotations

import os

import pytest

from debian_repo_scrape.exc import FileRequestError, HashInvalid
from debian_repo_scrape.navigation import BaseNavigator, PredefinedSuitesNavigator
from debian_repo_scrape.utils import clear_response_cache
from debian_repo_scrape.verify import (
    IGNORE_MISSING,
    RAISE_EXCEPTION,
    RAISE_EXCEPTION_IMPORTANT_FILE,
    VERIFY_IMPORTANT_ONLY,
    VerificationModes,
    verify_hash_sums,
    verify_release_signatures,
    verify_repo_integrity,
)

keyfile = "tests/public_key.gpg"


class RemoveFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self.file_content = b""

    def __enter__(self):
        with open(self.path, "rb") as f:
            self.file_content = f.read()
        os.remove(self.path)
        clear_response_cache()
        return self

    def __exit__(self, *_):
        with open(self.path, "wb") as f:
            f.write(self.file_content)
        clear_response_cache()


class ModifyFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self.file_content = b""

    def __enter__(self):
        with open(self.path, "rb") as f:
            self.file_content = f.read()
        with open(self.path, "wb") as f:
            f.write(self.file_content + b"\n\n\n1234")

        clear_response_cache()
        return self

    def __exit__(self, *_):
        with open(self.path, "wb") as f:
            f.write(self.file_content)
        clear_response_cache()


IMPORTANT_FILES = (
    "tests/repo/pool/main/p/poem/poem_1.0_all.deb",
    "tests/repo/dists/mx/main/binary-amd64/Packages.gz",
    "tests/repo/dists/mx/main/binary-amd64/Packages",
)
NON_IMPORTANT_FILES = ("tests/repo/dists/mx/main/binary-amd64/Release",)
ANY_FILES = (*IMPORTANT_FILES, *NON_IMPORTANT_FILES)


def __tuple_combinations(t1: tuple, t2: tuple) -> list[tuple]:
    res = []
    for e1 in t1:
        for e2 in t2:
            res.append((e1, e2))

    return res


@pytest.mark.parametrize("file,mode", __tuple_combinations(ANY_FILES, RAISE_EXCEPTION))
def test_hash_any_file(
    navigator: BaseNavigator,
    file: str,
    mode: VerificationModes,
):
    if file not in IMPORTANT_FILES and mode == VerificationModes.VERIFY_IMPORTANT_ONLY:
        with RemoveFile(file):
            verify_hash_sums(navigator, mode)

        with ModifyFile(file):
            verify_hash_sums(navigator, mode)
    else:
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(navigator, mode)

        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(navigator, mode)


@pytest.mark.parametrize("file,mode", __tuple_combinations(ANY_FILES, IGNORE_MISSING))
def test_hash_any_file_ignore_missing(
    navigator: BaseNavigator,
    file: str,
    caplog: pytest.LogCaptureFixture,
    mode: VerificationModes,
):

    if (
        file in IMPORTANT_FILES
        and mode == VerificationModes.IGNORE_MISSING_NON_IMPORTANT
    ):
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(navigator, mode)
    else:

        caplog.clear()
        with RemoveFile(file):
            verify_hash_sums(navigator, mode)
        assert len(caplog.records) == 0

    if file in NON_IMPORTANT_FILES and mode in VERIFY_IMPORTANT_ONLY:
        with ModifyFile(file):
            verify_hash_sums(navigator, mode)
    else:
        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(navigator, mode)


@pytest.mark.parametrize(
    "file,mode",
    __tuple_combinations(
        IMPORTANT_FILES, (*RAISE_EXCEPTION_IMPORTANT_FILE, *VERIFY_IMPORTANT_ONLY)
    ),
)
def test_hash_important_file(
    navigator: BaseNavigator, file: str, mode: VerificationModes
):
    if mode == VerificationModes.VERIFY_IMPORTANT_ONLY_IGNORE_MISSING:
        with RemoveFile(file):
            verify_hash_sums(navigator, mode)

    else:
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(navigator, mode)

    with pytest.raises(HashInvalid):
        with ModifyFile(file):
            verify_hash_sums(navigator, mode)


@pytest.mark.parametrize(
    "file,mode",
    __tuple_combinations(NON_IMPORTANT_FILES, RAISE_EXCEPTION_IMPORTANT_FILE),
)
def test_hash_non_important_file(
    navigator: BaseNavigator,
    file: str,
    caplog: pytest.LogCaptureFixture,
    mode: VerificationModes,
):

    if mode in IGNORE_MISSING:
        with RemoveFile(file):
            verify_hash_sums(navigator, mode)
        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(navigator, mode)
    else:
        caplog.clear()
        with RemoveFile(file):
            verify_hash_sums(navigator, mode)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"
        caplog.clear()
        with ModifyFile(file):
            verify_hash_sums(navigator, mode)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"


def test_signatures(navigator: BaseNavigator):

    verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release"):
            verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release.gpg"):
            verify_release_signatures(navigator, keyfile)


def test_hash_sums_suite_release_file(
    navigator: BaseNavigator, caplog: pytest.LogCaptureFixture
):
    with ModifyFile("tests/repo/dists/mx/Release"):
        verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)

    with ModifyFile("tests/repo/dists/mx/Release"):
        verify_hash_sums(navigator)

    if isinstance(navigator, PredefinedSuitesNavigator):

        with pytest.raises(FileRequestError):
            with RemoveFile("tests/repo/dists/mx/Release"):
                verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)
    else:
        caplog.clear()
        with pytest.raises(KeyError):
            with RemoveFile("tests/repo/dists/mx/Release"):
                verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)
        assert len(caplog.records) == 6
        for record in caplog.records:
            assert record.levelname == "WARNING"


def test_hash_sums(navigator: BaseNavigator):
    verify_hash_sums(navigator)

    with pytest.raises(ValueError):
        verify_hash_sums(navigator, "dawd34")


def test_verify_both(navigator: BaseNavigator):
    verify_repo_integrity(navigator, keyfile)
