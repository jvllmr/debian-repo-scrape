from __future__ import annotations

import os

import pytest
from pytest_lazyfixture import lazy_fixture

from debian_repo_scrape.exc import FileRequestError, HashInvalid
from debian_repo_scrape.navigation import (
    ApacheBrowseNavigator,
    BaseNavigator,
    PredefinedSuitesNavigator,
)
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
IMPORTANT_FILES_FLAT = (
    "tests/repo_flat/wheezy/Packages",
    "tests/repo_flat/bullseye/stable/Packages.gz",
    "tests/repo_flat/poem_1.0_all.deb",
)
NON_IMPORTANT_FILES = ("tests/repo/dists/mx/main/binary-amd64/Release",)
NON_IMPORTANT_FILES_FLAT = tuple()
ANY_FILES = IMPORTANT_FILES + NON_IMPORTANT_FILES
ANY_FILES_FLAT = NON_IMPORTANT_FILES_FLAT + IMPORTANT_FILES_FLAT


def __tuple_combinations(t1: tuple, t2: tuple, *args: tuple) -> list[tuple]:
    res = []
    for e1 in t1:
        for e2 in t2:
            res.append((e1, e2, *args))

    return res


@pytest.mark.parametrize(
    "file,mode,test_navigator,flat",
    __tuple_combinations(ANY_FILES, RAISE_EXCEPTION, lazy_fixture("navigator"), False)
    + __tuple_combinations(
        ANY_FILES_FLAT, RAISE_EXCEPTION, lazy_fixture("flat_navigator"), True
    ),
)
def test_hash_any_file(
    test_navigator: BaseNavigator, file: str, mode: VerificationModes, flat: bool
):
    if (
        file not in IMPORTANT_FILES + IMPORTANT_FILES_FLAT
        and mode == VerificationModes.VERIFY_IMPORTANT_ONLY
    ):
        with RemoveFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)

        with ModifyFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
    else:
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)

        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)


@pytest.mark.parametrize(
    "file,mode,test_navigator,flat",
    __tuple_combinations(ANY_FILES, IGNORE_MISSING, lazy_fixture("navigator"), False)
    + __tuple_combinations(
        ANY_FILES_FLAT, IGNORE_MISSING, lazy_fixture("flat_navigator"), True
    ),
)
def test_hash_any_file_ignore_missing(
    test_navigator: BaseNavigator,
    file: str,
    caplog: pytest.LogCaptureFixture,
    mode: VerificationModes,
    flat: bool,
):

    if (
        file in IMPORTANT_FILES + IMPORTANT_FILES_FLAT
        and mode == VerificationModes.IGNORE_MISSING_NON_IMPORTANT
    ):
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)
    else:

        caplog.clear()
        with RemoveFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
        assert len(caplog.records) == 0

    if (
        file in NON_IMPORTANT_FILES + NON_IMPORTANT_FILES_FLAT
        and mode in VERIFY_IMPORTANT_ONLY
    ):
        with ModifyFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
    else:
        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)


@pytest.mark.parametrize(
    "file,mode,test_navigator,flat",
    __tuple_combinations(
        IMPORTANT_FILES,
        RAISE_EXCEPTION_IMPORTANT_FILE + VERIFY_IMPORTANT_ONLY,
        lazy_fixture("navigator"),
        False,
    )
    + __tuple_combinations(
        IMPORTANT_FILES_FLAT,
        RAISE_EXCEPTION_IMPORTANT_FILE + VERIFY_IMPORTANT_ONLY,
        lazy_fixture("flat_navigator"),
        True,
    ),
)
def test_hash_important_file(
    test_navigator: BaseNavigator, file: str, mode: VerificationModes, flat: bool
):
    if mode == VerificationModes.VERIFY_IMPORTANT_ONLY_IGNORE_MISSING:
        with RemoveFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)

    else:
        with pytest.raises(FileRequestError):
            with RemoveFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)

    with pytest.raises(HashInvalid):
        with ModifyFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)


@pytest.mark.parametrize(
    "file,mode,test_navigator,flat",
    __tuple_combinations(
        NON_IMPORTANT_FILES,
        RAISE_EXCEPTION_IMPORTANT_FILE,
        lazy_fixture("navigator"),
        False,
    ),
)
def test_hash_non_important_file(
    test_navigator: BaseNavigator,
    file: str,
    caplog: pytest.LogCaptureFixture,
    mode: VerificationModes,
    flat: bool,
):

    if mode in IGNORE_MISSING:
        with RemoveFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
        with pytest.raises(HashInvalid):
            with ModifyFile(file):
                verify_hash_sums(test_navigator, mode, flat_repo=flat)
    else:
        caplog.clear()
        with RemoveFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"
        caplog.clear()
        with ModifyFile(file):
            verify_hash_sums(test_navigator, mode, flat_repo=flat)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"


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


@pytest.mark.parametrize(
    ["test_navigator", "flat"],
    [
        (lazy_fixture("navigator"), False),
        (lazy_fixture("flat_navigator"), True),
    ],
)
def test_hash_sums(test_navigator: BaseNavigator, flat: bool):
    verify_hash_sums(test_navigator, flat_repo=flat)

    with pytest.raises(ValueError):
        verify_hash_sums(test_navigator, mode="dawd34", flat_repo=flat)


@pytest.mark.parametrize(
    ["test_navigator", "path", "flat"],
    [
        (lazy_fixture("navigator"), "tests/repo/dists/mx/", False),
        (lazy_fixture("flat_navigator"), "tests/repo_flat/", True),
    ],
)
def test_verify_signatures(test_navigator: BaseNavigator, path: str, flat: bool):

    verify_release_signatures(test_navigator, keyfile, flat)

    with open(keyfile, "rb") as f:
        verify_release_signatures(test_navigator, f, flat)

    with open(keyfile, "rb") as f:
        verify_release_signatures(test_navigator, f.read(), flat)

    with pytest.raises(TypeError):
        verify_release_signatures(test_navigator, [], flat)

    if flat and isinstance(test_navigator, ApacheBrowseNavigator):
        with RemoveFile(f"{path}Release"):
            verify_release_signatures(test_navigator, keyfile, flat)
    else:
        with pytest.raises(FileRequestError):
            with RemoveFile(f"{path}Release"):
                verify_release_signatures(test_navigator, keyfile, flat)

    with pytest.raises(FileRequestError):
        with RemoveFile(f"{path}Release.gpg"):
            verify_release_signatures(test_navigator, keyfile, flat)

    with pytest.raises(FileRequestError):
        with RemoveFile(f"{path}InRelease"):
            verify_release_signatures(test_navigator, keyfile, flat)


@pytest.mark.parametrize(
    ["test_navigator", "flat"],
    [
        (lazy_fixture("navigator"), False),
        (lazy_fixture("flat_navigator"), True),
    ],
)
def test_verify_both(test_navigator: BaseNavigator, flat: bool):
    verify_repo_integrity(test_navigator, keyfile, flat_repo=flat)
