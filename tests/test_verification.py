import os

import pytest

from debian_repo_scrape.exc import FileRequestError, HashInvalid
from debian_repo_scrape.navigation import BaseNavigator, PredefinedSuitesNavigator
from debian_repo_scrape.utils import clear_response_cache
from debian_repo_scrape.verify import (
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


def test_signatures(navigator: BaseNavigator):

    verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release"):
            verify_release_signatures(navigator, keyfile)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/Release.gpg"):
            verify_release_signatures(navigator, keyfile)


def test_hash_sums_deb_file(navigator: BaseNavigator):
    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/pool/main/p/poem/poem_1.0_all.deb"):
            verify_hash_sums(navigator)

    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/pool/main/p/poem/poem_1.0_all.deb"):
            verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/pool/main/p/poem/poem_1.0_all.deb"):
            verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)


def test_hash_sums_packages_file(
    navigator: BaseNavigator, caplog: pytest.LogCaptureFixture
):
    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/main/binary-amd64/Packages"):
            verify_hash_sums(navigator)

    with pytest.raises(FileRequestError):
        with RemoveFile("tests/repo/dists/mx/main/binary-amd64/Packages"):
            verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)

    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/dists/mx/main/binary-amd64/Packages.gz"):
            verify_hash_sums(navigator)

    with pytest.raises(HashInvalid):
        with ModifyFile("tests/repo/dists/mx/main/binary-amd64/Packages"):
            verify_hash_sums(navigator)


def test_hash_sums_release_file(
    navigator: BaseNavigator, caplog: pytest.LogCaptureFixture
):
    with ModifyFile("tests/repo/dists/mx/Release"):
        verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)

    with ModifyFile("tests/repo/dists/mx/Release"):
        verify_hash_sums(navigator)

    with ModifyFile("tests/repo/dists/mx/main/binary-amd64/Release"):
        caplog.clear()
        verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"
    with RemoveFile("tests/repo/dists/mx/main/binary-amd64/Release"):
        caplog.clear()
        verify_hash_sums(navigator, VerificationModes.RAISE_IMPORTANT_ONLY)
        assert len(caplog.records) == 3
        for record in caplog.records:
            assert record.levelname == "WARNING"

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
